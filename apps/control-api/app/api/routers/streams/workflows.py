"""
SSE stream for workflow status events.

Clients subscribe to a workflow's event channel and receive real-time status
updates published by temporal-workers via the SSEBroker. The generator exits
cleanly when the client disconnects, preventing subscriber queue leaks.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse

from app.api.deps.auth import get_stream_principal
from app.api.deps.resources import (
    get_sse_broker,
    maybe_get_database_pool,
    maybe_get_temporal_gateway,
)
from app.auth.principals import Principal
from app.services.procedure_status import load_procedure_status
from app.services.temporal_gateway import TemporalGateway

router = APIRouter()


@router.get("/{workflow_id}", operation_id="stream_workflow_status")
async def stream_workflow_status(
    workflow_id: str,
    request: Request,
    principal: Principal = Depends(get_stream_principal),
    broker = Depends(get_sse_broker),
    gateway: TemporalGateway | None = Depends(maybe_get_temporal_gateway),
    pool = Depends(maybe_get_database_pool),
) -> EventSourceResponse:
    """
    Open a Server-Sent Events stream for a specific workflow execution.

    Events are published by temporal-workers (or any component with access to
    the SSEBroker) and forwarded verbatim to the subscriber. The stream closes
    when either the workflow emits a ``__CLOSE__`` sentinel or the client
    disconnects.
    """
    procedure = await load_procedure_status(
        workflow_id,
        gateway=gateway,
        pool=pool,
    )
    if procedure is None:
        if gateway is None and pool is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="procedure stream is temporarily unavailable",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Procedure '{workflow_id}' not found",
        )
    if procedure.tenant_id and not principal.can_access_tenant(procedure.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to procedure '{workflow_id}' is not permitted",
        )

    async def event_generator():
        async for event in broker.subscribe(workflow_id):
            if await request.is_disconnected():
                break
            yield {"data": event}

    return EventSourceResponse(event_generator())
