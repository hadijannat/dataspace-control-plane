from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar

from dataspace_control_plane_core.domains._shared.events import DomainEvent
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId


@dataclass(frozen=True)
class NegotiationStarted(DomainEvent):
    event_type: ClassVar[str] = "contracts.negotiation_started"
    negotiation_id: AggregateId = field(default_factory=lambda: AggregateId(""))
    tenant_id: TenantId = field(default_factory=lambda: TenantId(""))
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId(""))
    counterparty_id: str = ""
    asset_id: str = ""


@dataclass(frozen=True)
class OfferSubmitted(DomainEvent):
    event_type: ClassVar[str] = "contracts.offer_submitted"
    negotiation_id: AggregateId = field(default_factory=lambda: AggregateId(""))
    tenant_id: TenantId = field(default_factory=lambda: TenantId(""))
    offer_id: str = ""
    policy_id: str = ""


@dataclass(frozen=True)
class AgreementConcluded(DomainEvent):
    event_type: ClassVar[str] = "contracts.agreement_concluded"
    negotiation_id: AggregateId = field(default_factory=lambda: AggregateId(""))
    tenant_id: TenantId = field(default_factory=lambda: TenantId(""))
    agreement_id: str = ""
    concluded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class NegotiationTerminated(DomainEvent):
    event_type: ClassVar[str] = "contracts.negotiation_terminated"
    negotiation_id: AggregateId = field(default_factory=lambda: AggregateId(""))
    tenant_id: TenantId = field(default_factory=lambda: TenantId(""))
    reason: str = ""


@dataclass(frozen=True)
class EntitlementRevoked(DomainEvent):
    event_type: ClassVar[str] = "contracts.entitlement_revoked"
    entitlement_id: AggregateId = field(default_factory=lambda: AggregateId(""))
    tenant_id: TenantId = field(default_factory=lambda: TenantId(""))
    agreement_id: str = ""
    reason: str = ""
