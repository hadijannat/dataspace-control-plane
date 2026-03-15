from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OnboardingStartInput:
    tenant_id: str
    legal_entity_id: str
    legal_entity_name: str
    bpnl: str
    jurisdiction: str
    contact_email: str
    connector_url: str
    pack_id: str = "catena-x"
    idempotency_key: str = ""


@dataclass(frozen=True)
class OnboardingResult:
    workflow_id: str
    status: str
    registration_ref: str = ""
    bpnl: str = ""
    wallet_did: str = ""
    connector_binding_id: str = ""
    compliance_baseline_ref: str = ""


@dataclass(frozen=True)
class OnboardingStatusQuery:
    phase: str
    blocking_reason: str
    external_refs: dict[str, str]
    next_required_action: str
    is_complete: bool


@dataclass
class OnboardingCarryState:
    """Carry-over state for Continue-As-New boundaries."""
    phase: str
    registration_ref: str
    approval_ref: str
    bpnl: str
    wallet_ref: str
    connector_ref: str
    compliance_ref: str
    dedupe_ids: set[str]
    iteration: int = 0
