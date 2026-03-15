"""
Operator procedure launch and status endpoints.
All mutations return 202 with a workflow handle — never block on completion.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.api.deps.resources import (
    get_database_pool,
    get_idempotency_store,
    maybe_get_database_pool,
    maybe_get_temporal_gateway,
    get_procedure_catalog,
    get_temporal_gateway,
)
from app.api.deps.auth import get_current_principal
from app.application.commands.procedures import StartProcedureCommand
from app.application.dto.procedures import (
    ProcedureHandleDTO,
    ProcedureListDTO,
    ProcedureStatusDTO,
)
from app.auth.principals import Principal
from app.auth.tenant_context import TenantScope
from app.services import audit
from app.services import read_models
from app.services.procedure_catalog import ProcedureCatalog
from app.services.procedure_status import load_procedure_status
from app.services.temporal_gateway import TemporalGateway

router = APIRouter()

# Tenant scope dependency — reads tenant_id from path/query params.
_tenant_scope = TenantScope(tenant_id_param="tenant_id")


class StartProcedureRequest(BaseModel):
    procedure_type: str = Field(..., description="e.g. company-onboarding, connector-bootstrap")
    tenant_id: str
    legal_entity_id: str | None = None
    payload: dict = Field(default_factory=dict)
    idempotency_key: str | None = None


@router.post(
    "/start",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ProcedureHandleDTO,
    operation_id="operator_start_procedure",
)
async def start_procedure(
    body: StartProcedureRequest,
    request: Request,
    principal: Principal = Depends(get_current_principal),
    gateway: TemporalGateway = Depends(get_temporal_gateway),
    procedure_catalog: ProcedureCatalog = Depends(get_procedure_catalog),
    idempotency_store = Depends(get_idempotency_store),
) -> ProcedureHandleDTO:
    """
    Start a durable procedure. Returns immediately with a workflow handle.
    The actual work executes in temporal-workers.

    Idempotency: if an ``idempotency_key`` is provided and a result was
    already stored for it within the TTL window, the cached handle is
    returned without starting a second workflow.
    """
    correlation_id: str | None = getattr(request.state, "correlation_id", None)

    # Tenant authorisation — principal must have access to the requested tenant.
    if not principal.can_access_tenant(body.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to tenant '{body.tenant_id}' is not permitted",
        )

    # Idempotency check — return cached result if the key has been seen before.
    if body.idempotency_key:
        cached = await idempotency_store.check(body.idempotency_key)
        if cached is not None:
            return ProcedureHandleDTO(**cached)

    # Build command.
    cmd = StartProcedureCommand(
        procedure_type=body.procedure_type,
        tenant_id=body.tenant_id,
        legal_entity_id=body.legal_entity_id,
        payload=body.payload,
        idempotency_key=body.idempotency_key,
        actor_subject=principal.subject,
    )

    # Dispatch to Temporal via gateway.
    try:
        handle = await gateway.start_procedure(cmd, procedure_catalog)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        if "already" in str(exc).lower() and "workflow" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A matching workflow is already running",
            ) from exc
        raise

    workflow_id = handle.id

    # Emit audit event.
    await audit.emit(
        event_type="procedure.started",
        actor_subject=principal.subject,
        tenant_id=body.tenant_id,
        resource_type="procedure",
        resource_id=workflow_id,
        metadata={
            "procedure_type": body.procedure_type,
            "correlation_id": correlation_id,
            "idempotency_key": body.idempotency_key,
        },
    )

    result = ProcedureHandleDTO(
        workflow_id=workflow_id,
        procedure_type=body.procedure_type,
        tenant_id=body.tenant_id,
        status="STARTED",
        poll_url=f"/api/v1/operator/procedures/{workflow_id}",
        stream_url=f"/api/v1/streams/workflows/{workflow_id}",
        correlation_id=correlation_id,
    )

    # Cache result for idempotency on future duplicate requests.
    if body.idempotency_key:
        await idempotency_store.store(body.idempotency_key, result.model_dump())

    return result


@router.get(
    "/",
    operation_id="operator_list_procedures",
    response_model=ProcedureListDTO,
)
async def list_procedures(
    tenant_id: str = Depends(_tenant_scope),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = 50,
    offset: int = 0,
    pool = Depends(get_database_pool),
) -> ProcedureListDTO:
    rows = await read_models.list_procedures(
        pool,
        tenant_id=tenant_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    total = await read_models.count_procedures(
        pool,
        tenant_id=tenant_id,
        status=status_filter,
    )
    return ProcedureListDTO(
        items=[
            ProcedureStatusDTO(
                workflow_id=row["workflow_id"],
                procedure_type=row.get("procedure_type", ""),
                tenant_id=row.get("tenant_id", ""),
                status=row.get("status", "RUNNING"),
                result=row.get("result"),
                failure_message=row.get("failure_message"),
                search_attributes=row.get("search_attributes", {}) or {},
                started_at=row.get("started_at").isoformat() if row.get("started_at") else None,
                updated_at=row.get("updated_at").isoformat() if row.get("updated_at") else None,
            )
            for row in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{workflow_id}",
    operation_id="operator_get_procedure_status",
    response_model=ProcedureStatusDTO,
)
async def get_procedure_status(
    workflow_id: str,
    principal: Principal = Depends(get_current_principal),
    gateway: TemporalGateway | None = Depends(maybe_get_temporal_gateway),
    pool = Depends(maybe_get_database_pool),
) -> ProcedureStatusDTO:
    """
    Poll procedure status.

    Queries Temporal for a live status snapshot via the ``get_status``
    workflow query. If Temporal is unreachable or returns nothing, falls back
    to the read-model projection.
    """
    status_snapshot = await load_procedure_status(
        workflow_id,
        gateway=gateway,
        pool=pool,
    )
    if status_snapshot is None:
        if gateway is None and pool is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="procedure status is temporarily unavailable",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procedure '{workflow_id}' not found",
        )
    if status_snapshot.tenant_id and not principal.can_access_tenant(status_snapshot.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to procedure '{workflow_id}' is not permitted",
        )
    return status_snapshot
