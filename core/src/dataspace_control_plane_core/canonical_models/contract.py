"""
Canonical contract models — normalized DSP negotiation and agreement artifacts.
"""
from __future__ import annotations
from datetime import datetime
from pydantic import field_validator

from .common import CanonicalBase
from .enums import NegotiationState
from .identity import DidUri


class AssetRef(CanonicalBase):
    """Normalized reference to a data asset."""
    asset_id: str
    connector_id: str
    catalog_id: str | None = None


class CounterpartyRef(CanonicalBase):
    """Normalized counterparty reference."""
    participant_id: str   # BPN or DID
    did: DidUri | None = None
    connector_url: str | None = None


class OfferRef(CanonicalBase):
    """Reference to a catalog offer snapshot."""
    offer_id: str
    policy_id: str
    asset: AssetRef
    provider: CounterpartyRef
    valid_until: datetime | None = None


class NegotiationTranscriptRef(CanonicalBase):
    """Reference to the full negotiation transcript (stored externally)."""
    negotiation_id: str
    storage_uri: str
    message_count: int = 0


class AgreementRef(CanonicalBase):
    """Reference to a concluded agreement."""
    agreement_id: str
    policy_snapshot_id: str
    asset: AssetRef
    provider: CounterpartyRef
    consumer: CounterpartyRef
    concluded_at: datetime


class AgreementSnapshot(CanonicalBase):
    """Immutable snapshot of an agreement as it was at conclusion time."""
    agreement_id: str
    raw_policy_id: str     # ID of the CanonicalPolicy snapshot at conclusion
    asset: AssetRef
    concluded_at: datetime
    state: NegotiationState = NegotiationState.FINALIZED


class EntitlementRef(CanonicalBase):
    """Reference to a usage entitlement derived from an agreement."""
    entitlement_id: str
    agreement_id: str
    tenant_id: str
    legal_entity_id: str
    asset_id: str
    purpose: str
    counterparty_id: str
    valid_from: datetime
    valid_to: datetime | None = None
