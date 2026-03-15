"""Domain events for the metering_finops domain."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar

from dataspace_control_plane_core.domains._shared.events import DomainEvent
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from .model.enums import MeteringDimension, QuotaStatus


@dataclass(frozen=True)
class UsageEventRecorded(DomainEvent):
    event_type: ClassVar[str] = "metering_finops.usage_event_recorded"
    ledger_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
    event_id: str = ""
    dimension: MeteringDimension = MeteringDimension.API_CALLS
    quantity: int = 0


@dataclass(frozen=True)
class LedgerFinalized(DomainEvent):
    event_type: ClassVar[str] = "metering_finops.ledger_finalized"
    ledger_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId("__unset__"))


@dataclass(frozen=True)
class QuotaLimitSet(DomainEvent):
    event_type: ClassVar[str] = "metering_finops.quota_limit_set"
    allocation_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
    dimension: MeteringDimension = MeteringDimension.API_CALLS
    limit: int = 0


@dataclass(frozen=True)
class QuotaExceeded(DomainEvent):
    event_type: ClassVar[str] = "metering_finops.quota_exceeded"
    allocation_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
    dimension: MeteringDimension = MeteringDimension.API_CALLS
    current_usage: int = 0
    limit: int = 0
