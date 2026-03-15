"""
Transport DTOs used in API request/response bodies.
These are ONLY for the HTTP contract — never expose domain entities directly.
"""
from pydantic import BaseModel


class CommandAccepted(BaseModel):
    """Standard 202 response for any workflow-starting command."""
    workflow_id: str
    status: str = "ACCEPTED"
    poll_url: str
    stream_url: str
    correlation_id: str | None = None
