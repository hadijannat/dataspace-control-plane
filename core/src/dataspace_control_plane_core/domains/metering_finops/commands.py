"""Command objects for the metering_finops domain."""
from __future__ import annotations
from dataclasses import dataclass

from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from .model.value_objects import UsageEvent, QuotaLimit


@dataclass(frozen=True)
class RecordUsageEventCommand:
    """Append a usage event to a tenant's metering ledger."""
    tenant_id: TenantId
    ledger_id: AggregateId
    event: UsageEvent
    actor: ActorRef


@dataclass(frozen=True)
class FinalizeLedgerCommand:
    """Close the billing period for a ledger (no further events may be appended)."""
    tenant_id: TenantId
    ledger_id: AggregateId
    actor: ActorRef


@dataclass(frozen=True)
class SetQuotaLimitCommand:
    """Create or replace a quota limit for a dimension within a tenant/legal entity."""
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    limit: QuotaLimit
    actor: ActorRef
