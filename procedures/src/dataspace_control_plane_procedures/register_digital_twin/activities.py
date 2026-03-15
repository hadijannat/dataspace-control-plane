from __future__ import annotations

from dataclasses import dataclass, field

from temporalio import activity


# ── Input/Result dataclasses ──────────────────────────────────────────────────

@dataclass
class ShellValidateInput:
    tenant_id: str
    aas_id: str
    shell_descriptor: dict
    submodel_refs: list[dict]
    semantic_id: str
    pack_id: str


@dataclass
class ShellValidateResult:
    ok: bool
    warnings: list[str] = field(default_factory=list)
    requires_review: bool = False
    ambiguous_semantic_id: str = ""


@dataclass
class ShellUpsertInput:
    tenant_id: str
    aas_id: str
    shell_descriptor: dict
    pack_id: str
    idempotency_key: str = ""


@dataclass
class ShellUpsertResult:
    shell_id: str


@dataclass
class SubmodelUpsertInput:
    tenant_id: str
    shell_id: str
    submodel_refs: list[dict]
    pack_id: str
    idempotency_key: str = ""


@dataclass
class SubmodelUpsertResult:
    submodel_ids: list[str] = field(default_factory=list)


@dataclass
class RegistryRegInput:
    tenant_id: str
    shell_id: str
    aas_id: str
    global_asset_id: str
    submodel_ids: list[str]
    pack_id: str
    aas_registry_url: str = ""
    idempotency_key: str = ""


@dataclass
class RegistryRegResult:
    registry_url: str


@dataclass
class AccessRuleInput:
    tenant_id: str
    shell_id: str
    legal_entity_id: str
    pack_id: str
    idempotency_key: str = ""


@dataclass
class AccessRuleResult:
    rule_ids: list[str] = field(default_factory=list)


@dataclass
class VerifyReadbackInput:
    tenant_id: str
    shell_id: str
    aas_registry_url: str
    pack_id: str


@dataclass
class VerifyReadbackResult:
    ok: bool
    reason: str = ""


@dataclass
class TwinEvidenceInput:
    tenant_id: str
    legal_entity_id: str
    aas_id: str
    shell_id: str
    registry_url: str
    idempotency_key: str = ""


@dataclass
class TwinEvidenceResult:
    evidence_ref: str


@dataclass
class DeregisterInput:
    tenant_id: str
    shell_id: str
    submodel_ids: list[str]
    reason: str = "compensation"


# ── Activity definitions ──────────────────────────────────────────────────────

@activity.defn
async def validate_canonical_shell(inp: ShellValidateInput) -> ShellValidateResult:
    """Validate the shell/submodel descriptor against canonical AAS rules."""
    raise NotImplementedError("validate_canonical_shell activity must be implemented by adapter layer")


@activity.defn
async def upsert_aas_shell(inp: ShellUpsertInput) -> ShellUpsertResult:
    """Upsert the AAS shell descriptor to the AAS server; returns shell_id."""
    activity.heartbeat("upsert_aas_shell:started")
    raise NotImplementedError("upsert_aas_shell activity must be implemented by adapter layer")


@activity.defn
async def upsert_submodels(inp: SubmodelUpsertInput) -> SubmodelUpsertResult:
    """Batch upsert submodels to the AAS server; returns submodel_ids."""
    activity.heartbeat("upsert_submodels:started")
    raise NotImplementedError("upsert_submodels activity must be implemented by adapter layer")


@activity.defn
async def register_descriptor_in_registry(inp: RegistryRegInput) -> RegistryRegResult:
    """Register the shell descriptor in the AAS registry; returns registry_url."""
    raise NotImplementedError("register_descriptor_in_registry activity must be implemented by adapter layer")


@activity.defn
async def bind_access_rules(inp: AccessRuleInput) -> AccessRuleResult:
    """Attach policy/access rules to the AAS shell; returns rule_ids."""
    raise NotImplementedError("bind_access_rules activity must be implemented by adapter layer")


@activity.defn
async def verify_readback_from_registry(inp: VerifyReadbackInput) -> VerifyReadbackResult:
    """Fetch the shell back from the registry to confirm registration is visible."""
    raise NotImplementedError("verify_readback_from_registry activity must be implemented by adapter layer")


@activity.defn
async def record_twin_evidence(inp: TwinEvidenceInput) -> TwinEvidenceResult:
    """Emit an immutable audit record for the twin registration event."""
    raise NotImplementedError("record_twin_evidence activity must be implemented by adapter layer")


@activity.defn
async def deregister_shell(inp: DeregisterInput) -> None:
    """Compensation: deregister the shell and submodels from the AAS server and registry."""
    raise NotImplementedError("deregister_shell activity must be implemented by adapter layer")


ALL_ACTIVITIES = [
    validate_canonical_shell,
    upsert_aas_shell,
    upsert_submodels,
    register_descriptor_in_registry,
    bind_access_rules,
    verify_readback_from_registry,
    record_twin_evidence,
    deregister_shell,
]
