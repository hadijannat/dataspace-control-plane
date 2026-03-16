from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps.auth import get_current_principal
from app.api.deps.resources import get_procedure_catalog, maybe_get_database_pool, maybe_get_temporal_gateway
from app.api.schemas.streams import StreamTicketRequest, StreamTicketResponse
from app.auth.principals import Principal
from app.services.procedure_catalog import ProcedureCatalog
from app.services.procedure_status import load_procedure_status
from app.services.stream_tickets import mint_stream_ticket
from app.services.temporal_gateway import TemporalGateway
from app.settings import settings

router = APIRouter()


@router.post(
    "/tickets",
    response_model=StreamTicketResponse,
    operation_id="issue_stream_ticket",
)
async def issue_stream_ticket(
    body: StreamTicketRequest,
    principal: Principal = Depends(get_current_principal),
    catalog: ProcedureCatalog = Depends(get_procedure_catalog),
    gateway: TemporalGateway | None = Depends(maybe_get_temporal_gateway),
    pool=Depends(maybe_get_database_pool),
) -> StreamTicketResponse:
    snapshot = await load_procedure_status(
        body.workflow_id,
        catalog=catalog,
        gateway=gateway,
        pool=pool,
    )
    if snapshot is None:
        if gateway is None and pool is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="procedure stream is temporarily unavailable",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procedure '{body.workflow_id}' not found",
        )
    if snapshot.tenant_id and not principal.can_access_tenant(snapshot.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to procedure '{body.workflow_id}' is not permitted",
        )
    return StreamTicketResponse(
        ticket=mint_stream_ticket(
            principal,
            workflow_id=body.workflow_id,
            tenant_id=snapshot.tenant_id,
        ),
        expires_in_seconds=settings.stream_ticket_ttl_seconds,
    )
