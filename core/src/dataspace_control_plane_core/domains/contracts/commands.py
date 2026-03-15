from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId, AggregateId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.canonical_models.contract import CounterpartyRef, AssetRef


@dataclass(frozen=True)
class StartNegotiationCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    counterparty: CounterpartyRef
    asset: AssetRef
    initial_offer_id: str
    policy_id: str
    actor: ActorRef


@dataclass(frozen=True)
class SubmitOfferCommand:
    tenant_id: TenantId
    negotiation_id: AggregateId
    offer_id: str
    policy_id: str
    valid_until: datetime | None
    actor: ActorRef


@dataclass(frozen=True)
class ConcludeAgreementCommand:
    tenant_id: TenantId
    negotiation_id: AggregateId
    agreement_id: str
    policy_snapshot_id: str
    concluded_at: datetime
    actor: ActorRef


@dataclass(frozen=True)
class TerminateNegotiationCommand:
    tenant_id: TenantId
    negotiation_id: AggregateId
    reason: str
    actor: ActorRef


@dataclass(frozen=True)
class RevokeEntitlementCommand:
    tenant_id: TenantId
    entitlement_id: AggregateId
    reason: str
    actor: ActorRef
