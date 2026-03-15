"""
SSE stream for workflow status events.

Clients subscribe to a workflow execution and receive status snapshots derived
from shared runtime state (Temporal and read models). This is safe across
multiple API replicas because every subscriber polls the same durable sources.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse

from app.api.deps.auth import get_stream_principal
from app.api.deps.resources import (
    maybe_get_database_pool,
    maybe_get_temporal_gateway,
)
from app.auth.principals import Principal
from app.services.procedure_status import load_procedure_status
from app.services.temporal_gateway import TemporalGateway
from app.services.workflow_streams import iter_workflow_status_events

router = APIRouter()


@router.get("/{workflow_id}", operation_id="stream_workflow_status")
async def stream_workflow_status(
    workflow_id: str,
    request: Request,
    principal: Principal = Depends(get_stream_principal),
    gateway: TemporalGateway | None = Depends(maybe_get_temporal_gateway),
    pool = Depends(maybe_get_database_pool),
) -> EventSourceResponse:
    """
    Open a Server-Sent Events stream for a specific workflow execution.

    Events are derived from shared workflow status snapshots. The stream closes
    when the workflow reaches a terminal state or the client disconnects.
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
        async for event in iter_workflow_status_events(
            workflow_id,
            gateway=gateway,
            pool=pool,
            should_stop=request.is_disconnected,
        ):
            yield {"event": "status", "data": event}

    return EventSourceResponse(event_generator())
