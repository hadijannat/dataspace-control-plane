"""
Domain event base class.
Aggregates return lists of DomainEvent; the outbox pattern in adapters persists and dispatches them.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar
from uuid import UUID, uuid4

from .ids import TenantId, LegalEntityId
from .correlation import CorrelationContext


@dataclass(frozen=True)
class DomainEvent:
    """
    Immutable base for all domain events.
    Subclass and add fields; do not add methods that mutate state.
    """
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: TenantId | None = None
    legal_entity_id: LegalEntityId | None = None
    correlation: CorrelationContext | None = None

    # Subclasses must declare this to aid routing/serialization
    event_type: ClassVar[str] = "DomainEvent"

    def __init_subclass__(cls, event_type: str = "", **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if event_type:
            cls.event_type = event_type
