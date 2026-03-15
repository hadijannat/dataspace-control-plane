from __future__ import annotations

from dataclasses import dataclass, field

from temporalio import activity


# ── Input/Result dataclasses ──────────────────────────────────────────────────

@dataclass
class MappingSnapshotInput:
    tenant_id: str
    source_schema_id: str
    global_asset_id: str
    idempotency_key: str = ""


@dataclass
class MappingSnapshotResult:
    snapshot_id: str


@dataclass
class SourceReadinessInput:
    tenant_id: str
    global_asset_id: str
    asset_binding_id: str


@dataclass
class SourceReadinessResult:
    ok: bool
    reason: str = ""


@dataclass
class PolicyCompileInput:
    tenant_id: str
    policy_template_id: str
    pack_id: str
    asset_binding_id: str
    idempotency_key: str = ""


@dataclass
class PolicyCompileResult:
    policy_id: str
    lossy: bool = False


@dataclass
class AssetPublishInput:
    tenant_id: str
    legal_entity_id: str
    asset_binding_id: str
    revision: str
    global_asset_id: str
    mapping_snapshot_id: str
    compiled_policy_id: str
    pack_id: str
    catalog_endpoint: str = ""
    idempotency_key: str = ""


@dataclass
class AssetPublishResult:
    offer_id: str


@dataclass
class VisibilityCheckInput:
    tenant_id: str
    offer_id: str
    pack_id: str


@dataclass
class VisibilityCheckResult:
    visible: bool
    url: str = ""


@dataclass
class PublicationEvidenceInput:
    tenant_id: str
    legal_entity_id: str
    asset_binding_id: str
    revision: str
    offer_id: str
    discoverability_url: str
    idempotency_key: str = ""


@dataclass
class PublicationEvidenceResult:
    evidence_ref: str


@dataclass
class RetractInput:
    tenant_id: str
    offer_id: str
    reason: str = "compensation"


# ── Activity definitions ──────────────────────────────────────────────────────

@activity.defn
async def fetch_mapping_snapshot(inp: MappingSnapshotInput) -> MappingSnapshotResult:
    """Fetch schema mapping for source → canonical; returns snapshot_id."""
    raise NotImplementedError("fetch_mapping_snapshot activity must be implemented by adapter layer")


@activity.defn
async def validate_source_readiness(inp: SourceReadinessInput) -> SourceReadinessResult:
    """Check that the data source is accessible and ready for publication."""
    raise NotImplementedError("validate_source_readiness activity must be implemented by adapter layer")


@activity.defn
async def compile_policy(inp: PolicyCompileInput) -> PolicyCompileResult:
    """Compile canonical policy template to DSP format; returns policy_id and lossy flag."""
    raise NotImplementedError("compile_policy activity must be implemented by adapter layer")


@activity.defn
async def publish_asset_offer(inp: AssetPublishInput) -> AssetPublishResult:
    """Publish asset + offer to dataspace catalog; returns offer_id."""
    activity.heartbeat("publish_asset_offer:started")
    raise NotImplementedError("publish_asset_offer activity must be implemented by adapter layer")


@activity.defn
async def run_consumer_visibility_check(inp: VisibilityCheckInput) -> VisibilityCheckResult:
    """Consumer-side smoke test to confirm the offer is discoverable."""
    raise NotImplementedError("run_consumer_visibility_check activity must be implemented by adapter layer")


@activity.defn
async def record_publication_evidence(inp: PublicationEvidenceInput) -> PublicationEvidenceResult:
    """Emit an immutable audit record for the publication event."""
    raise NotImplementedError("record_publication_evidence activity must be implemented by adapter layer")


@activity.defn
async def retract_asset_offer(inp: RetractInput) -> None:
    """Compensation: retract a previously published asset offer from the catalog."""
    activity.heartbeat("retract_asset_offer:started")
    raise NotImplementedError("retract_asset_offer activity must be implemented by adapter layer")


ALL_ACTIVITIES = [
    fetch_mapping_snapshot,
    validate_source_readiness,
    compile_policy,
    publish_asset_offer,
    run_consumer_visibility_check,
    record_publication_evidence,
    retract_asset_offer,
]
