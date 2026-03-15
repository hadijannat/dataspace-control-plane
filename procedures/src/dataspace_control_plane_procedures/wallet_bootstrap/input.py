from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WalletStartInput:
    tenant_id: str
    legal_entity_id: str
    bpnl: str
    wallet_profile: str = "default"
    trust_anchor_url: str = ""
    idempotency_key: str = ""


@dataclass
class WalletResult:
    workflow_id: str
    status: str
    wallet_ref: str = ""
    wallet_did: str = ""
    credential_ids: list[str] = field(default_factory=list)


@dataclass
class WalletStatusQuery:
    wallet_state: str
    wallet_did: str
    credential_count: int
    is_bound: bool


@dataclass
class WalletCarryState:
    wallet_state: str
    wallet_ref: str
    wallet_did: str
    credential_ids: list[str]
    dedupe_ids: set[str]
    iteration: int = 0
