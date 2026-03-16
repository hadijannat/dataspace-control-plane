from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from dataspace_control_plane_adapters.infrastructure.temporal_client.errors import (
    WorkflowAlreadyStartedError,
)

from app.api.deps.auth import get_current_principal
from app.api.deps.resources import (
    get_procedure_catalog,
    get_start_procedure_service,
    maybe_get_database_pool,
    maybe_get_temporal_gateway,
)
from app.api.schemas.common import AcceptedResponse
from app.api.schemas.public_procedures import PublicStartProcedureRequest
from app.application.dto.procedures import ProcedureStatusDTO
from app.auth.principals import Principal
from app.services.procedure_status import load_procedure_status
from app.services.start_procedure_service import (
    IdempotencyConflictError,
    StartProcedureService,
)
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
    service: StartProcedureService = Depends(get_start_procedure_service),
) -> AcceptedResponse:
    correlation_id: str | None = getattr(request.state, "correlation_id", None)
    effective_idempotency_key = _resolve_idempotency_key(body, idempotency_key_header)

    try:
        result = await service.start(
            procedure_type=body.procedure_type,
            tenant_id=body.tenant_id,
            legal_entity_id=body.legal_entity_id,
            payload=body.payload,
            idempotency_key=effective_idempotency_key,
            principal=principal,
            correlation_id=correlation_id,
            poll_url_template="/api/v1/public/procedures/{workflow_id}",
            audit_event_type="public.procedure.started",
        )
        return AcceptedResponse(
            workflow_id=result.workflow_id,
            status=result.status,
            poll_url=result.poll_url,
            stream_url=result.stream_url,
            correlation_id=result.correlation_id,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except IdempotencyConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except WorkflowAlreadyStartedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A matching workflow is already running",
        ) from exc


@router.get(
    "/procedures/{workflow_id}",
    response_model=ProcedureStatusDTO,
    operation_id="public_get_procedure_status",
)
async def get_public_procedure_status(
    workflow_id: str,
    principal: Principal = Depends(get_current_principal),
    catalog = Depends(get_procedure_catalog),
    gateway: TemporalGateway | None = Depends(maybe_get_temporal_gateway),
    pool=Depends(maybe_get_database_pool),
) -> ProcedureStatusDTO:
    snapshot = await load_procedure_status(
        workflow_id,
        catalog=catalog,
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
