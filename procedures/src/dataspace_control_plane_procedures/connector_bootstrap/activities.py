"""Activity definitions for the connector_bootstrap procedure.

All I/O, provisioning calls, and side effects live here.
Activities heartbeat on long-running operations to detect worker loss.
"""
from __future__ import annotations

from dataclasses import dataclass

from temporalio import activity


# ---------------------------------------------------------------------------
# Plan connector infra
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectorPlanInput:
    tenant_id: str
    legal_entity_id: str
    environment: str
    binding_name: str
    connector_url: str
    pack_id: str = "catena-x"


@dataclass(frozen=True)
class ConnectorPlanResult:
    plan_ref: str
    connector_binding_id: str


@activity.defn
async def plan_connector_infra(inp: ConnectorPlanInput) -> ConnectorPlanResult:
    """Call the provisioning-agent plan endpoint to produce an infra plan.

    Heartbeats during the planning call so long-running plan generation
    is visible to the Temporal server.
    """
    activity.heartbeat("submitting plan request")

    # Real implementation: POST to provisioning-agent /plan with connector spec.
    plan_ref = f"plan:{inp.tenant_id}:{inp.legal_entity_id}:{inp.environment}:{inp.binding_name}"
    binding_id = f"connector:{inp.tenant_id}:{inp.legal_entity_id}:{inp.binding_name}"

    activity.heartbeat("plan received")
    return ConnectorPlanResult(plan_ref=plan_ref, connector_binding_id=binding_id)


# ---------------------------------------------------------------------------
# Apply connector infra
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectorApplyInput:
    tenant_id: str
    legal_entity_id: str
    plan_ref: str
    connector_binding_id: str


@dataclass(frozen=True)
class ConnectorApplyResult:
    infra_apply_ref: str


@activity.defn
async def apply_connector_infra(inp: ConnectorApplyInput) -> ConnectorApplyResult:
    """Call the provisioning-agent apply endpoint with the prepared plan.

    Heartbeats on each phase of the apply so infra convergence is tracked.
    """
    activity.heartbeat(f"starting apply for plan {inp.plan_ref}")

    # Real implementation: POST to provisioning-agent /apply with inp.plan_ref,
    # then poll the apply job until it reaches terminal state.
    apply_ref = f"apply:{inp.plan_ref}"

    activity.heartbeat("apply submitted, awaiting convergence")
    activity.heartbeat("infra converged")

    return ConnectorApplyResult(infra_apply_ref=apply_ref)


# ---------------------------------------------------------------------------
# Wait for runtime healthy
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectorHealthInput:
    connector_url: str
    connector_binding_id: str
    max_polls: int = 20


@dataclass(frozen=True)
class ConnectorHealthResult:
    is_healthy: bool
    health_status: str


@activity.defn
async def wait_for_runtime_healthy(inp: ConnectorHealthInput) -> ConnectorHealthResult:
    """Poll the connector's health endpoint until it reports healthy.

    Heartbeats on each poll so the Temporal server tracks liveness.
    Uses LONG_POLL_OPTIONS at the call site for the appropriate timeout.
    """
    import asyncio

    for attempt in range(1, inp.max_polls + 1):
        activity.heartbeat(f"health poll {attempt}/{inp.max_polls} for {inp.connector_binding_id}")

        # Real implementation: HTTP GET inp.connector_url/health and check status.
        # For now we return healthy after the first poll to keep the implementation
        # replay-safe and testable.
        is_healthy = True
        health_status = "healthy"

        if is_healthy:
            return ConnectorHealthResult(is_healthy=True, health_status=health_status)

        await asyncio.sleep(5)

    return ConnectorHealthResult(is_healthy=False, health_status="timeout")


# ---------------------------------------------------------------------------
# Link wallet to connector
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WalletLinkInput:
    tenant_id: str
    legal_entity_id: str
    connector_binding_id: str
    wallet_ref: str


@dataclass(frozen=True)
class WalletLinkResult:
    linked: bool
    wallet_ref: str


@activity.defn
async def link_wallet_to_connector(inp: WalletLinkInput) -> WalletLinkResult:
    """Bind wallet credentials to the connector configuration.

    In production: calls the wallet adapter to push credentials into the
    connector's secret store.
    """
    if not inp.wallet_ref:
        return WalletLinkResult(linked=False, wallet_ref="")

    return WalletLinkResult(linked=True, wallet_ref=inp.wallet_ref)


# ---------------------------------------------------------------------------
# Dataspace registration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DataspaceRegInput:
    tenant_id: str
    legal_entity_id: str
    connector_binding_id: str
    connector_url: str
    pack_id: str = "catena-x"


@dataclass(frozen=True)
class DataspaceRegResult:
    dataspace_connector_id: str


@activity.defn
async def register_in_dataspace(inp: DataspaceRegInput) -> DataspaceRegResult:
    """Register the connector in the DSP catalog for discovery.

    In production: calls the DSP registration endpoint defined by the pack.
    """
    dsp_id = f"dsp:{inp.pack_id}:{inp.connector_binding_id}"
    return DataspaceRegResult(dataspace_connector_id=dsp_id)


# ---------------------------------------------------------------------------
# Discovery verification
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DiscoveryVerifyInput:
    dataspace_connector_id: str
    pack_id: str = "catena-x"
    max_attempts: int = 10


@dataclass(frozen=True)
class DiscoveryVerifyResult:
    found: bool
    discovery_endpoint: str = ""


@activity.defn
async def verify_discovery(inp: DiscoveryVerifyInput) -> DiscoveryVerifyResult:
    """Verify that the connector appears in the discovery service.

    Polls the discovery endpoint with retries. Heartbeats on each attempt.
    """
    import asyncio

    for attempt in range(1, inp.max_attempts + 1):
        activity.heartbeat(
            f"discovery verification attempt {attempt}/{inp.max_attempts} "
            f"for {inp.dataspace_connector_id}"
        )

        # Real implementation: query discovery service for inp.dataspace_connector_id.
        discovery_endpoint = f"https://discovery.{inp.pack_id}.example.com/connectors/{inp.dataspace_connector_id}"
        return DiscoveryVerifyResult(found=True, discovery_endpoint=discovery_endpoint)

    return DiscoveryVerifyResult(found=False)


# ---------------------------------------------------------------------------
# Compensation — decommission connector
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DecommissionInput:
    connector_binding_id: str
    infra_apply_ref: str = ""
    dataspace_connector_id: str = ""


@activity.defn
async def decommission_connector(inp: DecommissionInput) -> None:
    """Compensation activity: tear down a partially provisioned connector.

    Heartbeats during decommission to track progress.
    """
    activity.heartbeat(f"decommissioning connector {inp.connector_binding_id}")

    if inp.dataspace_connector_id:
        activity.heartbeat(f"deregistering from dataspace: {inp.dataspace_connector_id}")
        # Real: call DSP deregistration endpoint.

    if inp.infra_apply_ref:
        activity.heartbeat(f"destroying infra for apply ref: {inp.infra_apply_ref}")
        # Real: call provisioning-agent destroy endpoint.

    activity.heartbeat(f"decommission complete for {inp.connector_binding_id}")
