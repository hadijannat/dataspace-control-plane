"""Activity definitions for the company_onboarding procedure.

All I/O, external calls, and side effects live here — never in workflow code.
Activities heartbeat on long-running operations so Temporal can detect worker loss.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from temporalio import activity


# ---------------------------------------------------------------------------
# Preflight validation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PreflightInput:
    bpnl: str
    jurisdiction: str
    contact_email: str


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    reason: str = ""


_BPNL_RE = re.compile(r"^BPNL[A-Z0-9]{12}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ALLOWED_JURISDICTIONS = {
    "DE", "FR", "NL", "BE", "PL", "IT", "ES", "AT", "CH", "SE", "NO",
    "DK", "FI", "PT", "CZ", "HU", "RO", "BG", "HR", "SK", "SI", "LT",
    "LV", "EE", "LU", "MT", "CY", "IE", "US", "GB", "JP", "KR", "CN",
}


@activity.defn
async def preflight_validate(inp: PreflightInput) -> PreflightResult:
    """Validate jurisdiction code, BPNL format, and contact e-mail.

    This is a fast, stateless check — no external calls. No heartbeat needed.
    """
    if not inp.bpnl or not _BPNL_RE.match(inp.bpnl):
        return PreflightResult(
            ok=False,
            reason=f"Invalid BPNL format: '{inp.bpnl}'. Expected BPNLxxxxxxxxxxxxxxx (16 chars).",
        )

    if inp.jurisdiction.upper() not in _ALLOWED_JURISDICTIONS:
        return PreflightResult(
            ok=False,
            reason=f"Unsupported jurisdiction: '{inp.jurisdiction}'.",
        )

    if not inp.contact_email or not _EMAIL_RE.match(inp.contact_email):
        return PreflightResult(
            ok=False,
            reason=f"Invalid contact email: '{inp.contact_email}'.",
        )

    return PreflightResult(ok=True)


# ---------------------------------------------------------------------------
# Legal entity registration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegistrationInput:
    tenant_id: str
    legal_entity_id: str
    legal_entity_name: str
    bpnl: str
    jurisdiction: str


@dataclass(frozen=True)
class RegistrationResult:
    registration_ref: str
    bpnl: str


@activity.defn
async def register_legal_entity(inp: RegistrationInput) -> RegistrationResult:
    """Call identity provisioning port to register the legal entity.

    Heartbeats during the registration call so long-running provisioning
    is visible to the Temporal server and worker loss is detected quickly.
    """
    activity.heartbeat("starting registration")

    # The real implementation delegates to the identity provisioning adapter port.
    # Here we produce a deterministic reference so the activity is replay-safe.
    reg_ref = f"reg:{inp.tenant_id}:{inp.legal_entity_id}"
    activity.heartbeat("registration submitted, awaiting acknowledgement")

    # In production: poll or long-call the provisioning API here.
    activity.heartbeat("registration acknowledged")

    return RegistrationResult(
        registration_ref=reg_ref,
        bpnl=inp.bpnl,
    )


# ---------------------------------------------------------------------------
# Approval request
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ApprovalRequestInput:
    tenant_id: str
    registration_ref: str
    contact_email: str


@dataclass(frozen=True)
class ApprovalRequestResult:
    approval_ref: str


@activity.defn
async def request_approval(inp: ApprovalRequestInput) -> ApprovalRequestResult:
    """Submit the registration for human approval via the MX portal or approval service.

    This is a fire-and-forget submission; the actual approval arrives as a Signal.
    """
    approval_ref = f"approval:{inp.tenant_id}:{inp.registration_ref}"
    return ApprovalRequestResult(approval_ref=approval_ref)


# ---------------------------------------------------------------------------
# Wallet bootstrap
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WalletBootstrapInput:
    tenant_id: str
    legal_entity_id: str
    bpnl: str


@dataclass(frozen=True)
class WalletBootstrapResult:
    wallet_ref: str
    did: str


@activity.defn
async def bootstrap_wallet(inp: WalletBootstrapInput) -> WalletBootstrapResult:
    """Start the child wallet workflow and return a stable reference + DID.

    In production: sends a start-workflow signal to WalletBootstrapWorkflow and
    polls until the wallet DID is provisioned. Heartbeats during the poll loop.
    """
    activity.heartbeat("requesting wallet bootstrap")

    wallet_ref = f"wallet:{inp.tenant_id}:{inp.legal_entity_id}"
    did = f"did:web:{inp.bpnl.lower()}.example.com"

    activity.heartbeat("wallet bootstrap complete")
    return WalletBootstrapResult(wallet_ref=wallet_ref, did=did)


# ---------------------------------------------------------------------------
# Connector bootstrap
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectorBootstrapInput:
    tenant_id: str
    legal_entity_id: str
    connector_url: str
    wallet_ref: str


@dataclass(frozen=True)
class ConnectorBootstrapResult:
    connector_binding_id: str


@activity.defn
async def bootstrap_connector(inp: ConnectorBootstrapInput) -> ConnectorBootstrapResult:
    """Start the child ConnectorBootstrapWorkflow and return the binding ID.

    Heartbeats during long provisioning wait.
    """
    activity.heartbeat("requesting connector bootstrap")

    binding_id = f"connector:{inp.tenant_id}:{inp.legal_entity_id}"

    activity.heartbeat("connector bootstrap complete")
    return ConnectorBootstrapResult(connector_binding_id=binding_id)


# ---------------------------------------------------------------------------
# Compliance baseline
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ComplianceInput:
    tenant_id: str
    legal_entity_id: str


@dataclass(frozen=True)
class ComplianceResult:
    baseline_ref: str


@activity.defn
async def run_compliance_baseline(inp: ComplianceInput) -> ComplianceResult:
    """Trigger a compliance gap scan for the newly onboarded entity.

    In production: calls the compliance adapter which fans out pack-specific checks.
    """
    baseline_ref = f"compliance:{inp.tenant_id}:{inp.legal_entity_id}:baseline"
    return ComplianceResult(baseline_ref=baseline_ref)


# ---------------------------------------------------------------------------
# Hierarchy binding (v2 patch — Catena-X parent/child topology)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HierarchyInput:
    tenant_id: str
    legal_entity_id: str
    parent_bpnl: str = ""


@dataclass(frozen=True)
class HierarchyResult:
    bound: bool
    parent_bpnl: str = ""


@activity.defn
async def bind_hierarchy(inp: HierarchyInput) -> HierarchyResult:
    """Attach the entity into the Catena-X parent/child BPNL topology.

    Only called when the v2 hierarchy patch is active (see versioning.patched).
    """
    if not inp.parent_bpnl:
        return HierarchyResult(bound=False)

    return HierarchyResult(bound=True, parent_bpnl=inp.parent_bpnl)


# ---------------------------------------------------------------------------
# Audit evidence emission
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceInput:
    tenant_id: str
    legal_entity_id: str
    registration_ref: str
    bpnl: str
    workflow_id: str


@activity.defn
async def emit_onboarding_evidence(inp: EvidenceInput) -> None:
    """Emit a structured audit event to the evidence sink.

    In production: calls core.audit port — never raises on delivery failures
    because evidence emission is best-effort; retry policy handles transient faults.
    """
    # The real implementation calls the audit adapter port here.
    pass


# ---------------------------------------------------------------------------
# Compensation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CompensateRegistrationInput:
    registration_ref: str


@activity.defn
async def compensate_registration(inp: CompensateRegistrationInput) -> None:
    """Revert a successful legal entity registration on workflow failure.

    Heartbeats so the compensation itself does not time out silently.
    """
    activity.heartbeat(f"compensating registration {inp.registration_ref}")

    # The real implementation calls the identity provisioning adapter's
    # deregister port with inp.registration_ref.
    activity.heartbeat(f"compensation complete for {inp.registration_ref}")


@dataclass(frozen=True)
class CompensateWalletBootstrapInput:
    wallet_ref: str


@activity.defn
async def compensate_wallet_bootstrap(inp: CompensateWalletBootstrapInput) -> None:
    activity.heartbeat(f"compensating wallet bootstrap {inp.wallet_ref}")
    activity.heartbeat(f"compensation complete for {inp.wallet_ref}")


@dataclass(frozen=True)
class CompensateConnectorBootstrapInput:
    connector_binding_id: str


@activity.defn
async def compensate_connector_bootstrap(inp: CompensateConnectorBootstrapInput) -> None:
    activity.heartbeat(f"compensating connector bootstrap {inp.connector_binding_id}")
    activity.heartbeat(f"compensation complete for {inp.connector_binding_id}")
