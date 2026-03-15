"""
Aggregate root base class with optimistic concurrency and domain event collection.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from uuid import UUID

from .ids import AggregateId, TenantId
from .events import DomainEvent


@dataclass
class AggregateRoot:
    """
    Base for all aggregate roots.
    - version: used for optimistic concurrency (start at 0, increment on save)
    - _pending_events: collected during the current command; drained by the repository
    Every aggregate root must be tenant-scoped.
    """
    id: AggregateId
    tenant_id: TenantId
    version: int = 0
    _pending_events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    def _raise_event(self, event: DomainEvent) -> None:
        """Record a domain event to be dispatched after successful persistence."""
        self._pending_events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Drain and return all pending domain events. Called by the repository outbox."""
        events = list(self._pending_events)
        self._pending_events.clear()
        return events
