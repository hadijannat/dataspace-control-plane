from __future__ import annotations

from dataclasses import dataclass, field

from temporalio import activity


# ── Input/Result dataclasses ──────────────────────────────────────────────────

@dataclass
class CreateWalletInput:
    tenant_id: str
    legal_entity_id: str
    bpnl: str
    wallet_profile: str
    trust_anchor_url: str
    idempotency_key: str = ""


@dataclass
class CreateWalletResult:
    wallet_ref: str
    wallet_service_url: str = ""


@dataclass
class RegisterDidInput:
    tenant_id: str
    wallet_ref: str
    trust_anchor_url: str
    idempotency_key: str = ""


@dataclass
class RegisterDidResult:
    did: str
    did_document_url: str = ""


@dataclass
class VerifMethodInput:
    tenant_id: str
    wallet_ref: str
    wallet_did: str
    idempotency_key: str = ""


@dataclass
class VerifMethodResult:
    verification_method_ids: list[str] = field(default_factory=list)


@dataclass
class CredReqInput:
    tenant_id: str
    wallet_ref: str
    wallet_did: str
    issuer_endpoint: str
    credential_types: list[str] = field(default_factory=list)
    idempotency_key: str = ""


@dataclass
class CredReqResult:
    request_ref: str


@dataclass
class PresVerifyInput:
    tenant_id: str
    wallet_ref: str
    wallet_did: str
    credential_ids: list[str] = field(default_factory=list)


@dataclass
class PresVerifyResult:
    ok: bool
    verification_report_ref: str = ""


@dataclass
class WalletBindInput:
    tenant_id: str
    wallet_ref: str
    wallet_did: str
    legal_entity_id: str
    idempotency_key: str = ""


@dataclass
class WalletBindResult:
    binding_id: str


@dataclass
class DecommissionWalletInput:
    tenant_id: str
    wallet_ref: str
    wallet_did: str
    reason: str = "compensation"


# ── Activity definitions ──────────────────────────────────────────────────────

@activity.defn
async def create_wallet(inp: CreateWalletInput) -> CreateWalletResult:
    """Call wallet service to provision a new wallet; returns wallet_ref."""
    activity.heartbeat("create_wallet:started")
    # Implementation delegates to adapter layer via injected client.
    raise NotImplementedError("create_wallet activity must be implemented by adapter layer")


@activity.defn
async def register_did(inp: RegisterDidInput) -> RegisterDidResult:
    """Call DID registrar to register a new DID for the wallet; returns did."""
    activity.heartbeat("register_did:started")
    raise NotImplementedError("register_did activity must be implemented by adapter layer")


@activity.defn
async def setup_verification_methods(inp: VerifMethodInput) -> VerifMethodResult:
    """Attach key material / verification methods to the DID document."""
    raise NotImplementedError("setup_verification_methods activity must be implemented by adapter layer")


@activity.defn
async def request_credential_from_issuer(inp: CredReqInput) -> CredReqResult:
    """Submit credential request to issuer; returns request_ref (async, callback expected)."""
    raise NotImplementedError("request_credential_from_issuer activity must be implemented by adapter layer")


@activity.defn
async def verify_credential_presentation(inp: PresVerifyInput) -> PresVerifyResult:
    """Perform presentation smoke test to verify issued credential is usable."""
    raise NotImplementedError("verify_credential_presentation activity must be implemented by adapter layer")


@activity.defn
async def bind_wallet_to_connector(inp: WalletBindInput) -> WalletBindResult:
    """Set wallet refs on connector config so the connector can use this wallet."""
    raise NotImplementedError("bind_wallet_to_connector activity must be implemented by adapter layer")


@activity.defn
async def decommission_wallet(inp: DecommissionWalletInput) -> None:
    """Compensation: decommission wallet and deregister DID."""
    activity.heartbeat("decommission_wallet:started")
    raise NotImplementedError("decommission_wallet activity must be implemented by adapter layer")


ALL_ACTIVITIES = [
    create_wallet,
    register_did,
    setup_verification_methods,
    request_credential_from_issuer,
    verify_credential_presentation,
    bind_wallet_to_connector,
    decommission_wallet,
]
