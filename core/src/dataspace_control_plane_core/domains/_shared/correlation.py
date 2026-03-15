"""
CorrelationContext: propagates request/workflow/causation chain across domain boundaries.
Every command and event should carry a CorrelationContext.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class CorrelationContext:
    """
    Carries identifiers that link a request/event chain:
    - correlation_id: stable across all steps of a single business operation
    - causation_id: ID of the event/command that caused this one
    - workflow_id: Temporal workflow execution ID (if this action is inside a workflow)
    - request_id: HTTP/gRPC request ID (outermost boundary)
    """
    correlation_id: UUID = field(default_factory=uuid4)
    causation_id: UUID | None = None
    workflow_id: str | None = None
    request_id: str | None = None

    @classmethod
    def new(cls) -> "CorrelationContext":
        """Create a fresh root-level correlation context."""
        return cls(correlation_id=uuid4())

    def caused_by(self, causation_id: UUID) -> "CorrelationContext":
        """Return a child context caused by the given event/command ID."""
        return CorrelationContext(
            correlation_id=self.correlation_id,
            causation_id=causation_id,
            workflow_id=self.workflow_id,
            request_id=self.request_id,
        )
