"""Aggregate root base class with optimistic concurrency and event buffering."""
from __future__ import annotations

from dataclasses import dataclass, field

from .events import DomainEvent
from .ids import AggregateId, TenantId


@dataclass
class AggregateRoot:
    """
    Base for tenant-scoped aggregate roots.

    ``version`` is reserved for optimistic concurrency in adapter repositories.
    """

    id: AggregateId
    tenant_id: TenantId
    version: int = 0
    _pending_events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    def _raise_event(self, event: DomainEvent) -> None:
        self._pending_events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._pending_events)
        self._pending_events.clear()
        return events

    def mark_persisted(self, version: int) -> None:
        """Update the aggregate version after a successful save."""
        self.version = version
