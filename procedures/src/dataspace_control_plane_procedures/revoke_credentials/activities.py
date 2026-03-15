"""Activity definitions for the revoke_credentials procedure.

All I/O, external calls, and side effects live here — never in workflow code.
Activities heartbeat on long-running operations so Temporal can detect worker loss.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from temporalio import activity


# ---------------------------------------------------------------------------
# Credential status update
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UpdateStatusInput:
    tenant_id: str
    credential_id: str
    credential_type: str
    revocation_reason: str
    revoked_by: str


@dataclass(frozen=True)
class UpdateStatusResult:
    revocation_ref: str


@activity.defn
async def update_credential_status(inp: UpdateStatusInput) -> UpdateStatusResult:
    """Mark the credential revoked in the trust domain status registry.

    Heartbeats during the write so worker loss is detected quickly.
    In production: calls the VC status list or StatusList2021 adapter port.
    """
    activity.heartbeat("submitting revocation to status registry")
    revocation_ref = f"revocation:{inp.tenant_id}:{inp.credential_id}"
    activity.heartbeat("revocation status recorded")
    return UpdateStatusResult(revocation_ref=revocation_ref)


# ---------------------------------------------------------------------------
# Connector/wallet binding propagation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PropagateBindingsInput:
    tenant_id: str
    credential_id: str
    credential_type: str
    revocation_ref: str


@dataclass(frozen=True)
class PropagateBindingsResult:
    binding_refs: list[str] = field(default_factory=list)


@activity.defn
async def propagate_to_connector_bindings(inp: PropagateBindingsInput) -> PropagateBindingsResult:
    """Remove the revoked credential from all connector and wallet bindings.

    Heartbeats during the propagation sweep.
    In production: calls the connector adapter port to flush credential caches.
    """
    activity.heartbeat("querying connector bindings")
    binding_refs = [f"binding:{inp.tenant_id}:{inp.credential_id}:connector"]
    activity.heartbeat("bindings removed")
    return PropagateBindingsResult(binding_refs=binding_refs)


# ---------------------------------------------------------------------------
# Find dependent procedures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FindDependentsInput:
    tenant_id: str
    credential_id: str
    credential_type: str


@dataclass(frozen=True)
class FindDependentsResult:
    workflow_ids: list[str] = field(default_factory=list)


@activity.defn
async def find_dependent_procedures(inp: FindDependentsInput) -> FindDependentsResult:
    """Query Temporal visibility for workflows that reference this credential.

    In production: uses Temporal List API with a search attribute filter
    on credential_id or the relevant binding field.
    """
    # The real implementation queries Temporal ListWorkflowExecutions.
    workflow_ids: list[str] = []
    return FindDependentsResult(workflow_ids=workflow_ids)


# ---------------------------------------------------------------------------
# Notify dependent procedures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NotifyDependentsInput:
    tenant_id: str
    credential_id: str
    dependent_workflow_ids: list[str]
    revocation_ref: str


@dataclass(frozen=True)
class NotifyDependentsResult:
    notified_ids: list[str] = field(default_factory=list)


@activity.defn
async def notify_dependent_procedures(inp: NotifyDependentsInput) -> NotifyDependentsResult:
    """Signal each dependent workflow that the credential it holds has been revoked.

    In production: calls Temporal SignalWorkflowExecution for each workflow_id.
    """
    notified_ids: list[str] = []
    for wf_id in inp.dependent_workflow_ids:
        activity.heartbeat(f"notifying {wf_id}")
        # Real implementation: temporal_client.signal_workflow(wf_id, "credential_revoked", ...)
        notified_ids.append(wf_id)
    return NotifyDependentsResult(notified_ids=notified_ids)


# ---------------------------------------------------------------------------
# Freeze dependent procedures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FreezeDependentsInput:
    tenant_id: str
    credential_id: str
    dependent_workflow_ids: list[str]


@dataclass(frozen=True)
class FreezeDependentsResult:
    frozen_ids: list[str] = field(default_factory=list)


@activity.defn
async def freeze_dependent_procedures(inp: FreezeDependentsInput) -> FreezeDependentsResult:
    """Signal dependent procedures to pause execution until re-credentialing.

    In production: sends a pause/freeze signal to each dependent workflow.
    """
    frozen_ids: list[str] = []
    for wf_id in inp.dependent_workflow_ids:
        activity.heartbeat(f"freezing {wf_id}")
        # Real implementation: temporal_client.signal_workflow(wf_id, "pause", ...)
        frozen_ids.append(wf_id)
    return FreezeDependentsResult(frozen_ids=frozen_ids)


# ---------------------------------------------------------------------------
# Revocation evidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RevocationEvidenceInput:
    tenant_id: str
    credential_id: str
    credential_type: str
    revocation_reason: str
    revoked_by: str
    revocation_ref: str
    notified_procedure_ids: list[str]
    workflow_id: str


@dataclass(frozen=True)
class RevocationEvidenceResult:
    evidence_ref: str


@activity.defn
async def record_revocation_evidence(inp: RevocationEvidenceInput) -> RevocationEvidenceResult:
    """Emit a structured audit record covering the full revocation chain.

    In production: calls the core audit adapter port with the complete
    revocation event including all notified procedures and binding refs.
    """
    evidence_ref = f"evidence:revocation:{inp.tenant_id}:{inp.credential_id}"
    return RevocationEvidenceResult(evidence_ref=evidence_ref)
