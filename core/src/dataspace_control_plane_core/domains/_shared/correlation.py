"""Correlation metadata shared across commands, events, audit, and procedures."""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from .ids import WorkflowId, default_id_factory


@dataclass(frozen=True)
class CorrelationContext:
    """
    Correlates related operations without encoding runtime-specific types.

    ``correlation_id`` links all work for one business operation.
    ``causation_id`` points to the command/event that produced the current step.
    ``workflow_id`` references durable procedure execution when present.
    ``request_id`` links to the boundary request or envelope identifier.
    """

    correlation_id: UUID = field(default_factory=lambda: default_id_factory().new_event_id())
    causation_id: UUID | None = None
    workflow_id: WorkflowId | None = None
    request_id: str | None = None

    @classmethod
    def new(
        cls,
        workflow_id: WorkflowId | None = None,
        request_id: str | None = None,
    ) -> "CorrelationContext":
        return cls(
            correlation_id=default_id_factory().new_event_id(),
            workflow_id=workflow_id,
            request_id=request_id or default_id_factory().new_request_id(),
        )

    def caused_by(self, causation_id: UUID) -> "CorrelationContext":
        return CorrelationContext(
            correlation_id=self.correlation_id,
            causation_id=causation_id,
            workflow_id=self.workflow_id,
            request_id=self.request_id,
        )
