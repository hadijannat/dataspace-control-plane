from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from dataspace_control_plane_core.canonical_models.contract import CounterpartyRef, AssetRef
from .enums import NegotiationStatus, EntitlementStatus
from .value_objects import OfferSnapshot, AgreementRecord, TransferAuthorization


@dataclass
class NegotiationCase(AggregateRoot):
    """Tracks the full lifecycle of a DSP contract negotiation."""
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId(""))
    counterparty: CounterpartyRef | None = None
    asset: AssetRef | None = None
    status: NegotiationStatus = NegotiationStatus.PENDING
    offer_history: list[OfferSnapshot] = field(default_factory=list)
    agreement: AgreementRecord | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    concluded_at: datetime | None = None

    def submit_offer(self, offer: OfferSnapshot) -> None:
        self.offer_history.append(offer)
        self.status = NegotiationStatus.IN_PROGRESS

    def conclude_agreement(self, agreement: AgreementRecord) -> None:
        if self.agreement is not None:
            from dataspace_control_plane_core.domains._shared.errors import ConflictError
            raise ConflictError("NegotiationCase already has a concluded agreement")
        self.agreement = agreement
        self.status = NegotiationStatus.CONCLUDED
        self.concluded_at = datetime.now(timezone.utc)

    def terminate(self, reason: str) -> None:
        self.status = NegotiationStatus.TERMINATED


@dataclass
class Entitlement(AggregateRoot):
    """A usage entitlement derived from a concluded agreement."""
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId(""))
    agreement_id: str = ""
    asset_id: str = ""
    purpose: str = ""
    counterparty_id: str = ""
    status: EntitlementStatus = EntitlementStatus.ACTIVE
    valid_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_to: datetime | None = None

    def is_active(self, now: datetime) -> bool:
        if self.status != EntitlementStatus.ACTIVE:
            return False
        if self.valid_to and self.valid_to < now:
            return False
        return True

    def revoke(self) -> None:
        self.status = EntitlementStatus.REVOKED
