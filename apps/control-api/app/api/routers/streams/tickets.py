from fastapi import APIRouter, Depends

from app.api.deps.auth import get_current_principal
from app.api.schemas.streams import StreamTicketResponse
from app.auth.principals import Principal
from app.services.stream_tickets import mint_stream_ticket
from app.settings import settings

router = APIRouter()


@router.post(
    "/tickets",
    response_model=StreamTicketResponse,
    operation_id="issue_stream_ticket",
)
async def issue_stream_ticket(
    principal: Principal = Depends(get_current_principal),
) -> StreamTicketResponse:
    return StreamTicketResponse(
        ticket=mint_stream_ticket(principal),
        expires_in_seconds=settings.stream_ticket_ttl_seconds,
    )

