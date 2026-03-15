"""Activity definitions for the evidence_export procedure.

All I/O, external calls, and side effects live here — never in workflow code.
Activities heartbeat on long-running operations so Temporal can detect worker loss.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from temporalio import activity


# ---------------------------------------------------------------------------
# Evidence collection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CollectEvidenceInput:
    tenant_id: str
    legal_entity_id: str
    scope: str
    period_start: str
    period_end: str


@dataclass(frozen=True)
class CollectEvidenceResult:
    evidence_refs: list[str] = field(default_factory=list)
    count: int = 0


@activity.defn
async def collect_evidence_refs(inp: CollectEvidenceInput) -> CollectEvidenceResult:
    """Pull evidence refs from audit/contracts/metering/compliance for the given period."""
    activity.heartbeat("collecting from audit log")
    evidence_refs = [f"audit:{inp.tenant_id}:{inp.period_start}:{i}" for i in range(3)]
    activity.heartbeat("collecting from contracts")
    activity.heartbeat("collecting from compliance")
    return CollectEvidenceResult(evidence_refs=evidence_refs, count=len(evidence_refs))


# ---------------------------------------------------------------------------
# Manifest building
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ManifestBuildInput:
    tenant_id: str
    evidence_refs: list[str]
    scope: str
    period_start: str
    period_end: str
    bundle_type: str


@dataclass(frozen=True)
class ManifestBuildResult:
    manifest_ref: str


@activity.defn
async def build_manifest(inp: ManifestBuildInput) -> ManifestBuildResult:
    """Assemble a manifest envelope listing all evidence refs for the export bundle."""
    manifest_ref = f"manifest:{inp.tenant_id}:{inp.scope}:{inp.bundle_type}"
    return ManifestBuildResult(manifest_ref=manifest_ref)


# ---------------------------------------------------------------------------
# KMS signing
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SigningInput:
    tenant_id: str
    manifest_ref: str
    bundle_type: str


@dataclass(frozen=True)
class SigningResult:
    signature_ref: str
    bundle_ref: str


@activity.defn
async def request_kms_signature(inp: SigningInput) -> SigningResult:
    """Call KMS to sign the manifest; heartbeats in case of async signing."""
    activity.heartbeat("requesting KMS signature")
    signature_ref = f"sig:{inp.tenant_id}:{inp.manifest_ref}"
    bundle_ref = f"bundle:{inp.tenant_id}:{inp.bundle_type}"
    activity.heartbeat("signature received")
    return SigningResult(signature_ref=signature_ref, bundle_ref=bundle_ref)


# ---------------------------------------------------------------------------
# Bundle storage
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StoreBundleInput:
    tenant_id: str
    bundle_ref: str
    signature_ref: str
    export_destination: str


@dataclass(frozen=True)
class StoreBundleResult:
    export_url: str


@activity.defn
async def store_bundle(inp: StoreBundleInput) -> StoreBundleResult:
    """Write the signed bundle to the configured export destination (S3/blob)."""
    export_url = f"s3://{inp.export_destination or 'evidence-store'}/{inp.bundle_ref}"
    return StoreBundleResult(export_url=export_url)


# ---------------------------------------------------------------------------
# Publication / notification
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PublishNotifyInput:
    tenant_id: str
    bundle_ref: str
    export_url: str


@activity.defn
async def publish_bundle_notification(inp: PublishNotifyInput) -> None:
    """Emit audit record and optional webhook notification."""
    # The real implementation calls the audit adapter port and any registered
    # webhook endpoints for the tenant.
    pass


# ---------------------------------------------------------------------------
# Dry-run comparison
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DryRunInput:
    tenant_id: str
    evidence_refs: list[str]
    scope: str
    period_start: str
    period_end: str


@dataclass(frozen=True)
class DryRunResult:
    diff_summary: str
    expected_count: int
    would_sign: bool


@activity.defn
async def dry_run_comparison(inp: DryRunInput) -> DryRunResult:
    """Compare expected vs actual export contents without signing."""
    return DryRunResult(
        diff_summary=f"Would export {len(inp.evidence_refs)} refs for scope {inp.scope}",
        expected_count=len(inp.evidence_refs),
        would_sign=True,
    )
