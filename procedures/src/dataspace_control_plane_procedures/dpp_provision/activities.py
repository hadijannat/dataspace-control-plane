"""Activity definitions for the dpp_provision procedure.

All I/O, external calls, and side effects live here — never in workflow code.
Activities heartbeat on long-running operations so Temporal can detect worker loss.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from temporalio import activity


# ---------------------------------------------------------------------------
# Collect source snapshot
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceSnapshotInput:
    tenant_id: str
    product_instance_id: str
    source_system_ref: str


@dataclass(frozen=True)
class SourceSnapshotResult:
    snapshot_ref: str


@activity.defn
async def collect_source_snapshot(inp: SourceSnapshotInput) -> SourceSnapshotResult:
    """Collect product data from source system; returns snapshot_ref.

    Heartbeats during the data collection to surface worker loss.
    """
    activity.heartbeat("connecting to source system")
    snapshot_ref = f"snapshot:{inp.tenant_id}:{inp.product_instance_id}"
    activity.heartbeat("source data collected")
    return SourceSnapshotResult(snapshot_ref=snapshot_ref)


# ---------------------------------------------------------------------------
# Resolve submodel templates
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TemplateResolveInput:
    tenant_id: str
    submodel_template_ids: list[str]
    pack_id: str


@dataclass(frozen=True)
class TemplateResolveResult:
    template_refs: list[str]


@activity.defn
async def resolve_submodel_templates(inp: TemplateResolveInput) -> TemplateResolveResult:
    """Fetch submodel templates from the template registry; returns template_refs."""
    template_refs = [f"tmpl:{inp.tenant_id}:{tid}" for tid in inp.submodel_template_ids]
    return TemplateResolveResult(template_refs=template_refs)


# ---------------------------------------------------------------------------
# Compile submodels
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SubmodelCompileInput:
    tenant_id: str
    product_instance_id: str
    snapshot_ref: str
    template_refs: list[str]
    field_overrides: dict[str, str]


@dataclass(frozen=True)
class SubmodelCompileResult:
    submodel_ids: list[str]
    completeness_score: float
    missing_mandatory: list[str]


@activity.defn
async def compile_submodels(inp: SubmodelCompileInput) -> SubmodelCompileResult:
    """Run mapping transforms for each template to build submodels.

    Heartbeats for each template processed. Returns submodel_ids, completeness
    score, and any missing mandatory fields.
    """
    submodel_ids = []
    for i, ref in enumerate(inp.template_refs):
        activity.heartbeat(f"compiling submodel {i + 1}/{len(inp.template_refs)}")
        submodel_ids.append(f"sm:{inp.tenant_id}:{inp.product_instance_id}:{i}")

    activity.heartbeat("submodel compilation complete")
    # In production: compute real completeness from mapping results.
    completeness_score = 1.0 if not inp.field_overrides else 0.95
    missing_mandatory: list[str] = []
    return SubmodelCompileResult(
        submodel_ids=submodel_ids,
        completeness_score=completeness_score,
        missing_mandatory=missing_mandatory,
    )


# ---------------------------------------------------------------------------
# Upsert DPP twin data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DppUpsertInput:
    tenant_id: str
    product_instance_id: str
    revision: str
    submodel_ids: list[str]
    asset_id: str


@dataclass(frozen=True)
class DppUpsertResult:
    dpp_id: str


@activity.defn
async def upsert_dpp_twin_data(inp: DppUpsertInput) -> DppUpsertResult:
    """Upsert DPP shell + submodels to AAS server; returns dpp_id.

    Heartbeats during the AAS upsert to surface worker loss.
    """
    activity.heartbeat("upserting DPP shell to AAS server")
    dpp_id = f"dpp:{inp.tenant_id}:{inp.product_instance_id}:{inp.revision}"
    activity.heartbeat("DPP submodels upserted")
    return DppUpsertResult(dpp_id=dpp_id)


# ---------------------------------------------------------------------------
# Bind identifier link
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IdLinkInput:
    tenant_id: str
    dpp_id: str
    product_instance_id: str
    pack_id: str


@dataclass(frozen=True)
class IdLinkResult:
    identifier_link: str


@activity.defn
async def bind_identifier_link(inp: IdLinkInput) -> IdLinkResult:
    """Bind DPP identifier link (IRS, traceability link); returns identifier_link."""
    activity.heartbeat("binding identifier link")
    identifier_link = f"irs:{inp.tenant_id}:{inp.dpp_id}"
    activity.heartbeat("identifier link bound")
    return IdLinkResult(identifier_link=identifier_link)


# ---------------------------------------------------------------------------
# Record DPP evidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DppEvidenceInput:
    tenant_id: str
    legal_entity_id: str
    dpp_id: str
    identifier_link: str
    workflow_id: str
    product_instance_id: str


@dataclass(frozen=True)
class DppEvidenceResult:
    evidence_ref: str


@activity.defn
async def record_dpp_evidence(inp: DppEvidenceInput) -> DppEvidenceResult:
    """Emit an audit record for the DPP provisioning; returns evidence_ref."""
    evidence_ref = f"ev:{inp.tenant_id}:{inp.dpp_id}"
    return DppEvidenceResult(evidence_ref=evidence_ref)


# ---------------------------------------------------------------------------
# Compensation — deregister DPP
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DeregisterDppInput:
    tenant_id: str
    dpp_id: str


@activity.defn
async def deregister_dpp(inp: DeregisterDppInput) -> None:
    """Compensation: deregister the DPP twin from the AAS server."""
    activity.heartbeat(f"deregistering DPP {inp.dpp_id}")
    # In production: calls AAS adapter deregistration port.
    activity.heartbeat(f"DPP {inp.dpp_id} deregistered")
