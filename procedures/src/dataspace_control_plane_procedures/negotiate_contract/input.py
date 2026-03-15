from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NegotiationStartInput:
    tenant_id: str
    legal_entity_id: str
    offer_id: str
    counterparty_connector_id: str
    purpose: str
    asset_id: str
    policy_template_id: str
    pack_id: str = "default"
    idempotency_key: str = ""


@dataclass
class NegotiationResult:
    workflow_id: str
    status: str
    agreement_id: str = ""
    entitlement_id: str = ""
    transfer_auth_token: str = ""


@dataclass
class NegotiationStatusQuery:
    negotiation_state: str
    offer_id: str
    agreement_id: str
    blocking_reason: str
    next_action: str
    is_concluded: bool


@dataclass
class NegotiationCarryState:
    negotiation_state: str
    negotiation_ref: str
    agreement_id: str
    entitlement_id: str
    dedupe_ids: set[str]
    iteration: int = 0
