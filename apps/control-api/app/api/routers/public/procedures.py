from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.api.deps.auth import get_current_principal
from app.api.deps.resources import (
    get_idempotency_store,
    get_procedure_catalog,
    maybe_get_database_pool,
    maybe_get_temporal_gateway,
    get_temporal_gateway,
)
from app.api.schemas.common import AcceptedResponse
from app.api.schemas.public_procedures import PublicStartProcedureRequest
from app.application.commands.procedures import StartProcedureCommand
from app.application.dto.procedures import ProcedureStatusDTO
from app.auth.principals import Principal
from app.services import audit
from app.services.procedure_catalog import ProcedureCatalog
from app.services.procedure_status import load_procedure_status
from app.services.temporal_gateway import TemporalGateway

router = APIRouter()


def _resolve_idempotency_key(
    body: PublicStartProcedureRequest,
    header_value: str | None,
) -> str | None:
    return header_value or body.idempotency_key


@router.post(
    "/procedures/start",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AcceptedResponse,
    operation_id="public_start_procedure",
)
async def start_public_procedure(
    body: PublicStartProcedureRequest,
    request: Request,
    idempotency_key_header: str | None = Header(default=None, alias="Idempotency-Key"),
    principal: Principal = Depends(get_current_principal),
    gateway: TemporalGateway = Depends(get_temporal_gateway),
    procedure_catalog: ProcedureCatalog = Depends(get_procedure_catalog),
    idempotency_store=Depends(get_idempotency_store),
) -> AcceptedResponse:
    correlation_id: str | None = getattr(request.state, "correlation_id", None)
    effective_idempotency_key = _resolve_idempotency_key(body, idempotency_key_header)

    if not principal.can_access_tenant(body.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to tenant '{body.tenant_id}' is not permitted",
        )

    if effective_idempotency_key:
        cached = await idempotency_store.check(effective_idempotency_key)
        if cached is not None:
            return AcceptedResponse(
                workflow_id=cached["workflow_id"],
                status=cached["status"],
                poll_url=f"/api/v1/public/procedures/{cached['workflow_id']}",
                stream_url=f"/api/v1/streams/workflows/{cached['workflow_id']}",
                correlation_id=cached.get("correlation_id"),
            )

    command = StartProcedureCommand(
        procedure_type=body.procedure_type,
        tenant_id=body.tenant_id,
        legal_entity_id=body.legal_entity_id,
        payload=body.payload,
        idempotency_key=effective_idempotency_key,
        actor_subject=principal.subject,
    )

    try:
        handle = await gateway.start_procedure(command, procedure_catalog)
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

    response = AcceptedResponse(
        workflow_id=handle.id,
        status="STARTED",
        poll_url=f"/api/v1/public/procedures/{handle.id}",
        stream_url=f"/api/v1/streams/workflows/{handle.id}",
        correlation_id=correlation_id,
    )

    await audit.emit(
        event_type="public.procedure.started",
        actor_subject=principal.subject,
        tenant_id=body.tenant_id,
        resource_type="procedure",
        resource_id=handle.id,
        metadata={
            "procedure_type": body.procedure_type,
            "correlation_id": correlation_id,
            "idempotency_key": effective_idempotency_key,
        },
    )

    if effective_idempotency_key:
        await idempotency_store.store(
            effective_idempotency_key,
            {
                "workflow_id": response.workflow_id,
                "procedure_type": body.procedure_type,
                "tenant_id": body.tenant_id,
                "status": response.status,
                "correlation_id": response.correlation_id,
            },
        )

    return response


@router.get(
    "/procedures/{workflow_id}",
    response_model=ProcedureStatusDTO,
    operation_id="public_get_procedure_status",
)
async def get_public_procedure_status(
    workflow_id: str,
    principal: Principal = Depends(get_current_principal),
    gateway: TemporalGateway | None = Depends(maybe_get_temporal_gateway),
    pool=Depends(maybe_get_database_pool),
) -> ProcedureStatusDTO:
    snapshot = await load_procedure_status(
        workflow_id,
        gateway=gateway,
        pool=pool,
    )
    if snapshot is None:
        if gateway is None and pool is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="procedure status is temporarily unavailable",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procedure '{workflow_id}' not found",
        )
    if snapshot.tenant_id and not principal.can_access_tenant(snapshot.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to procedure '{workflow_id}' is not permitted",
        )
    return snapshot
