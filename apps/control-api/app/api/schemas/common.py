"""
Reusable request/response schemas shared across API routers.

These Pydantic models are for transport-layer concerns only — pagination
envelopes, generic accepted responses, and error shapes. Domain-specific
response shapes live in ``app/application/dto/``.
"""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """
    Standard query-string pagination parameters.

    Attributes
    ----------
    limit:
        Maximum number of items to return. Clamped between 1 and 200.
    offset:
        Number of items to skip. Must be non-negative.
    """

    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class AcceptedResponse(BaseModel):
    """
    Standard HTTP 202 response body for commands that start a workflow.

    Attributes
    ----------
    workflow_id:
        The Temporal workflow identifier for the accepted procedure.
    status:
        Always ``"STARTED"`` for 202 responses.
    poll_url:
        Relative URL to GET for the current procedure status.
    stream_url:
        Relative URL to subscribe to for real-time SSE status events.
    correlation_id:
        Echo of the ``X-Correlation-ID`` header from the request, when present.
    """

    workflow_id: str
    status: str = "STARTED"
    poll_url: str
    stream_url: str
    correlation_id: str | None = None


class ErrorDetail(BaseModel):
    """
    Standard error response body.

    Attributes
    ----------
    code:
        Machine-readable error code (SCREAMING_SNAKE_CASE).
    message:
        Human-readable description of the error.
    details:
        Optional structured context (field-level validation errors, etc.).
    """

    code: str
    message: str
    details: dict | None = None
