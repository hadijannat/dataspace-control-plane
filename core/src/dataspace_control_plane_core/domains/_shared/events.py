"""Immutable domain event primitives for aggregate outboxes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar
from uuid import UUID

from .correlation import CorrelationContext
from .ids import LegalEntityId, TenantId, default_id_factory
from .time import utc_now


@dataclass(frozen=True)
class DomainEvent:
    """
    Immutable base for all domain events.

    Adapters persist and dispatch these records, but event meaning is defined in
    ``core``.
    """

    event_id: UUID = field(default_factory=lambda: default_id_factory().new_event_id())
    occurred_at: datetime = field(default_factory=utc_now)
    tenant_id: TenantId | None = None
    legal_entity_id: LegalEntityId | None = None
    correlation: CorrelationContext | None = None

    event_type: ClassVar[str] = "DomainEvent"

    def __init_subclass__(cls, event_type: str = "", **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if event_type:
            cls.event_type = event_type
