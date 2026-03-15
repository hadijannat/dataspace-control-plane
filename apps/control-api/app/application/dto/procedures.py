"""
API response DTOs for procedure resources.

These Pydantic models define the JSON shapes returned to callers. They are
assembled by route handlers from service/gateway results and must never
expose internal domain entities directly.
"""
from typing import Any

from pydantic import BaseModel, Field


class ProcedureHandleDTO(BaseModel):
    """
    Immediate response returned when a procedure is accepted (HTTP 202).

    Contains all the information a caller needs to poll for completion or
    subscribe to the SSE stream.
    """

    workflow_id: str
    procedure_type: str
    tenant_id: str
    status: str
    poll_url: str
    stream_url: str
    correlation_id: str | None = None
    started_at: str | None = None


class ProcedureStatusDTO(BaseModel):
    """
    Full status snapshot of a procedure, returned by the poll endpoint.

    Attributes
    ----------
    status:
        One of ``RUNNING``, ``COMPLETED``, ``FAILED``, ``CANCELLED``,
        ``TIMED_OUT``.
    result:
        Workflow result payload when ``status == "COMPLETED"``, otherwise
        ``None``.
    failure_message:
        Human-readable failure description when ``status == "FAILED"``.
    search_attributes:
        Temporal search attributes attached to the workflow execution, useful
        for filtering in the Temporal UI.
    """

    workflow_id: str
    procedure_type: str
    tenant_id: str
    status: str
    result: Any | None = None
    failure_message: str | None = None
    search_attributes: dict[str, Any] = Field(default_factory=dict)
    started_at: str | None = None
    updated_at: str | None = None


class ProcedureListDTO(BaseModel):
    """
    Paginated list of procedure status snapshots.

    Attributes
    ----------
    items:
        Page of procedure status records.
    total:
        Total number of matching records (for pagination UI).
    limit:
        Page size used for this request.
    offset:
        Offset used for this request.
    """

    items: list[ProcedureStatusDTO]
    total: int
    limit: int
    offset: int
