"""EvidenceExportWorkflow — durable Temporal one-shot workflow.

Orchestrates the full evidence export lifecycle:
  collecting → manifest_built → signed → stored → published

Replay safety rules:
  - No datetime.now(), uuid4(), or random() calls in workflow code.
  - All I/O is delegated to activity functions.
  - Queries only read local state.
"""
from __future__ import annotations

from temporalio import workflow
from temporalio.exceptions import CancelledError

from dataspace_control_plane_procedures._shared.search_attributes import (
    TENANT_ID,
    LEGAL_ENTITY_ID,
    PROCEDURE_TYPE,
    STATUS,
    build_search_attribute_updates,
)
from dataspace_control_plane_procedures._shared.activity_options import (
    EXPORT_OPTIONS,
    RPC_OPTIONS,
)

from .input import EvidenceExportStartInput, EvidenceExportResult, EvidenceExportStatusQuery
from .state import EvidenceExportWorkflowState
from .errors import EvidenceCollectionError, EvidenceExportError
from .activities import (
    collect_evidence_refs,
    CollectEvidenceInput,
    build_manifest,
    ManifestBuildInput,
    request_kms_signature,
    SigningInput,
    store_bundle,
    StoreBundleInput,
    publish_bundle_notification,
    PublishNotifyInput,
    dry_run_comparison,
    DryRunInput,
)


@workflow.defn
class EvidenceExportWorkflow:
    """One-shot workflow: one instance per export request.

    Drives an evidence bundle through collection, manifest assembly,
    KMS signing, storage, and publication, then emits an audit event.
    """

    def __init__(self) -> None:
        self._state = EvidenceExportWorkflowState()

    # ------------------------------------------------------------------
    # Main run method
    # ------------------------------------------------------------------

    @workflow.run
    async def run(self, inp: EvidenceExportStartInput) -> EvidenceExportResult:
        # Publish search attributes so the workflow is discoverable.
        workflow.upsert_search_attributes(build_search_attribute_updates({
            TENANT_ID: inp.tenant_id,
            LEGAL_ENTITY_ID: inp.legal_entity_id,
            PROCEDURE_TYPE: "evidence-export",
            STATUS: "running",
        }))
        self._state.is_dry_run = inp.dry_run

        # Collect evidence refs
        self._state.phase = "collecting"
        collect_result = await workflow.execute_activity(
            collect_evidence_refs,
            CollectEvidenceInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                scope=inp.scope,
                period_start=inp.period_start,
                period_end=inp.period_end,
            ),
            **EXPORT_OPTIONS,
        )
        self._state.evidence_refs = collect_result.evidence_refs
        self._state.phase = "collected"

        # Build manifest
        manifest_result = await workflow.execute_activity(
            build_manifest,
            ManifestBuildInput(
                tenant_id=inp.tenant_id,
                evidence_refs=self._state.evidence_refs,
                scope=inp.scope,
                period_start=inp.period_start,
                period_end=inp.period_end,
                bundle_type=inp.bundle_type,
            ),
            **RPC_OPTIONS,
        )
        self._state.manifest_ref = manifest_result.manifest_ref
        self._state.phase = "manifest_built"

        # Dry run: compare and return early without signing or storing
        if inp.dry_run:
            dry_result = await workflow.execute_activity(
                dry_run_comparison,
                DryRunInput(
                    tenant_id=inp.tenant_id,
                    evidence_refs=self._state.evidence_refs,
                    scope=inp.scope,
                    period_start=inp.period_start,
                    period_end=inp.period_end,
                ),
                **RPC_OPTIONS,
            )
            self._state.dry_run_diff = dry_result.diff_summary
            workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "completed_dry_run"}))
            await workflow.wait_condition(workflow.all_handlers_finished)
            return EvidenceExportResult(
                workflow_id=workflow.info().workflow_id,
                status="completed_dry_run",
                evidence_count=dry_result.expected_count,
                dry_run=True,
            )

        # Sign the manifest via KMS
        sign_result = await workflow.execute_activity(
            request_kms_signature,
            SigningInput(
                tenant_id=inp.tenant_id,
                manifest_ref=self._state.manifest_ref,
                bundle_type=inp.bundle_type,
            ),
            **EXPORT_OPTIONS,
        )
        self._state.signature_ref = sign_result.signature_ref
        self._state.bundle_ref = sign_result.bundle_ref
        self._state.phase = "signed"

        # Store the signed bundle
        store_result = await workflow.execute_activity(
            store_bundle,
            StoreBundleInput(
                tenant_id=inp.tenant_id,
                bundle_ref=self._state.bundle_ref,
                signature_ref=self._state.signature_ref,
                export_destination=inp.export_destination,
            ),
            **RPC_OPTIONS,
        )
        self._state.export_url = store_result.export_url
        self._state.phase = "stored"

        # Publish audit notification
        await workflow.execute_activity(
            publish_bundle_notification,
            PublishNotifyInput(
                tenant_id=inp.tenant_id,
                bundle_ref=self._state.bundle_ref,
                export_url=self._state.export_url,
            ),
            **RPC_OPTIONS,
        )
        self._state.phase = "published"

        workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "completed"}))
        await workflow.wait_condition(workflow.all_handlers_finished)

        return EvidenceExportResult(
            workflow_id=workflow.info().workflow_id,
            status="completed",
            bundle_ref=self._state.bundle_ref,
            signature_ref=self._state.signature_ref,
            export_url=self._state.export_url,
            evidence_count=len(self._state.evidence_refs),
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @workflow.query
    def get_status(self) -> EvidenceExportStatusQuery:
        return EvidenceExportStatusQuery(
            phase=self._state.phase,
            evidence_count=len(self._state.evidence_refs),
            bundle_ref=self._state.bundle_ref,
            is_signed=bool(self._state.signature_ref),
        )
