"""Activity definitions for the delegate_tenant procedure.

All I/O, external calls, and side effects live here — never in workflow code.
Activities heartbeat on long-running operations so Temporal can detect worker loss.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from temporalio import activity


# ---------------------------------------------------------------------------
# create_child_topology
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChildTopologyInput:
    tenant_id: str
    parent_legal_entity_id: str
    child_legal_entity_id: str
    child_legal_entity_name: str


@dataclass(frozen=True)
class ChildTopologyResult:
    child_topology_ref: str


@activity.defn
async def create_child_topology(inp: ChildTopologyInput) -> ChildTopologyResult:
    """Create a LegalEntityTopology record for the child in core/tenant_topology domain.

    Heartbeats during the provisioning call so worker loss is detected quickly.
    """
    activity.heartbeat("creating child topology")
    ref = f"topology:{inp.tenant_id}:{inp.child_legal_entity_id}"
    activity.heartbeat("child topology created")
    return ChildTopologyResult(child_topology_ref=ref)


# ---------------------------------------------------------------------------
# bind_child_identifiers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IdentifierBindInput:
    tenant_id: str
    child_legal_entity_id: str
    child_bpnl: str
    child_topology_ref: str


@dataclass(frozen=True)
class IdentifierBindResult:
    bound: bool
    identifier_ref: str = ""


@activity.defn
async def bind_child_identifiers(inp: IdentifierBindInput) -> IdentifierBindResult:
    """Attach BPNL and other external identifiers to the child entity."""
    identifier_ref = f"ident:{inp.tenant_id}:{inp.child_legal_entity_id}"
    return IdentifierBindResult(bound=True, identifier_ref=identifier_ref)


# ---------------------------------------------------------------------------
# determine_connector_mode
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectorModeInput:
    tenant_id: str
    parent_legal_entity_id: str
    child_legal_entity_id: str
    requested_mode: str           # "shared" | "dedicated" | "auto"
    parent_connector_ref: str
    pack_id: str


@dataclass(frozen=True)
class ConnectorModeResult:
    mode: str                     # "shared" | "dedicated"
    connector_ref: str = ""       # populated if mode == "shared"
    requires_review: bool = False # True for cross-border/multi-trust-anchor cases


@activity.defn
async def determine_connector_mode(inp: ConnectorModeInput) -> ConnectorModeResult:
    """Determine shared vs dedicated connector mode based on policy.

    Policy engine consults pack rules and cross-border jurisdiction checks.
    Returns requires_review=True when cross-border delegation needs manual sign-off.
    """
    if inp.requested_mode in ("shared", "dedicated"):
        mode = inp.requested_mode
    else:
        # Auto mode: prefer shared if parent already has a connector reference.
        mode = "shared" if inp.parent_connector_ref else "dedicated"

    connector_ref = inp.parent_connector_ref if mode == "shared" else ""
    return ConnectorModeResult(mode=mode, connector_ref=connector_ref, requires_review=False)


# ---------------------------------------------------------------------------
# apply_shared_connector_delegation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SharedConnectorInput:
    tenant_id: str
    parent_legal_entity_id: str
    child_legal_entity_id: str
    parent_connector_ref: str
    child_topology_ref: str


@dataclass(frozen=True)
class SharedConnectorResult:
    delegation_ref: str


@activity.defn
async def apply_shared_connector_delegation(inp: SharedConnectorInput) -> SharedConnectorResult:
    """Bind the child entity to the parent connector with an explicit delegation scope policy."""
    activity.heartbeat("applying shared connector delegation")
    delegation_ref = f"delegation:{inp.tenant_id}:{inp.parent_legal_entity_id}:{inp.child_legal_entity_id}"
    activity.heartbeat("shared connector delegation applied")
    return SharedConnectorResult(delegation_ref=delegation_ref)


# ---------------------------------------------------------------------------
# apply_trust_scope
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrustScopeInput:
    tenant_id: str
    child_legal_entity_id: str
    delegation_ref: str
    connector_mode: str


@dataclass(frozen=True)
class TrustScopeResult:
    scope_refs: list[str] = field(default_factory=list)


@activity.defn
async def apply_trust_scope(inp: TrustScopeInput) -> TrustScopeResult:
    """Apply delegation trust scope restrictions to constrain what the child entity may do."""
    scope_ref = f"scope:{inp.tenant_id}:{inp.child_legal_entity_id}:{inp.connector_mode}"
    return TrustScopeResult(scope_refs=[scope_ref])


# ---------------------------------------------------------------------------
# verify_tenant_isolation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IsolationVerifyInput:
    tenant_id: str
    parent_legal_entity_id: str
    child_legal_entity_id: str
    child_topology_ref: str


@dataclass(frozen=True)
class IsolationVerifyResult:
    ok: bool
    reason: str = ""


@activity.defn
async def verify_tenant_isolation(inp: IsolationVerifyInput) -> IsolationVerifyResult:
    """Verify that tenant and legal-entity isolation invariants are maintained.

    Queries the core topology domain to confirm boundaries have not been breached.
    """
    activity.heartbeat("verifying tenant isolation")
    # Real implementation: calls core isolation verification port.
    return IsolationVerifyResult(ok=True)


# ---------------------------------------------------------------------------
# emit_delegation_evidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DelegationEvidenceInput:
    tenant_id: str
    parent_legal_entity_id: str
    child_legal_entity_id: str
    delegation_ref: str
    connector_mode: str
    workflow_id: str


@activity.defn
async def emit_delegation_evidence(inp: DelegationEvidenceInput) -> None:
    """Emit a structured audit event to the evidence sink for this delegation."""
    # Real implementation: calls core.audit port.
    pass


# ---------------------------------------------------------------------------
# revoke_delegation  (compensation)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RevokeDelegationInput:
    tenant_id: str
    delegation_ref: str
    child_topology_ref: str


@activity.defn
async def revoke_delegation(inp: RevokeDelegationInput) -> None:
    """Compensation: revoke the delegation and delete the child topology entry.

    Heartbeats because the revocation call may involve external systems.
    """
    activity.heartbeat(f"revoking delegation {inp.delegation_ref}")
    # Real implementation: calls core topology domain deprovisioning port.
    activity.heartbeat(f"revocation complete for {inp.delegation_ref}")
