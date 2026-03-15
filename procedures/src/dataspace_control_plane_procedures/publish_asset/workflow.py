from __future__ import annotations

from temporalio import workflow
from temporalio.exceptions import ApplicationError

from dataspace_control_plane_procedures._shared.activity_options import (
    PROVISIONING_OPTIONS,
    EXTERNAL_CALL_OPTIONS,
    RPC_OPTIONS,
)
from dataspace_control_plane_procedures._shared.search_attributes import (
    TENANT_ID,
    LEGAL_ENTITY_ID,
    PROCEDURE_TYPE,
    STATUS,
    ASSET_ID,
)
from dataspace_control_plane_procedures.publish_asset.input import (
    PublishAssetStartInput,
    PublishAssetResult,
    PublishAssetStatusQuery,
)
from dataspace_control_plane_procedures.publish_asset.state import PublishAssetWorkflowState
from dataspace_control_plane_procedures.publish_asset.messages import (
    ForceRepublish,
    ForceRepublishResult,
)
from dataspace_control_plane_procedures.publish_asset.activities import (
    fetch_mapping_snapshot,
    validate_source_readiness,
    compile_policy,
    publish_asset_offer,
    run_consumer_visibility_check,
    record_publication_evidence,
    MappingSnapshotInput,
    SourceReadinessInput,
    PolicyCompileInput,
    AssetPublishInput,
    VisibilityCheckInput,
    PublicationEvidenceInput,
)
from dataspace_control_plane_procedures.publish_asset.compensation import run_publish_compensation
from dataspace_control_plane_procedures.publish_asset.manifest import MANIFEST

_TERMINAL_PHASES = frozenset({"evidence_recorded", "failed"})


@workflow.defn
class PublishAssetWorkflow:
    """One-shot workflow: canonical snapshot → policy compile → publish → verify → evidence."""

    def __init__(self) -> None:
        self._state = PublishAssetWorkflowState()
        self._inp: PublishAssetStartInput | None = None
        self._force_republish_approved: bool = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @workflow.run
    async def run(self, inp: PublishAssetStartInput) -> PublishAssetResult:
        self._inp = inp

        workflow.upsert_search_attributes({
            TENANT_ID: [inp.tenant_id],
            LEGAL_ENTITY_ID: [inp.legal_entity_id],
            PROCEDURE_TYPE: [MANIFEST.workflow_type],
            ASSET_ID: [inp.global_asset_id],
            STATUS: ["running"],
        })

        try:
            await self._fetch_snapshot()
            await self._validate_readiness()
            await self._compile_policy()
            await self._publish()
            await self._verify_visibility()
            await self._record_evidence()
        except Exception:
            workflow.upsert_search_attributes({STATUS: ["failed"]})
            await run_publish_compensation(self._state, inp.tenant_id)
            raise

        workflow.upsert_search_attributes({STATUS: ["completed"]})

        await workflow.wait_condition(workflow.all_handlers_finished)

        return PublishAssetResult(
            workflow_id=workflow.info().workflow_id,
            status="completed",
            asset_offer_id=self._state.asset_offer_id,
            discoverability_url=self._state.discoverability_url,
            evidence_ref=self._state.evidence_ref,
        )

    # ── Steps ─────────────────────────────────────────────────────────────────

    async def _fetch_snapshot(self) -> None:
        assert self._inp is not None
        result = await workflow.execute_activity(
            fetch_mapping_snapshot,
            MappingSnapshotInput(
                tenant_id=self._inp.tenant_id,
                source_schema_id=self._inp.source_schema_id,
                global_asset_id=self._inp.global_asset_id,
                idempotency_key=self._inp.idempotency_key,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.mapping_snapshot_id = result.snapshot_id
        self._state.phase = "snapshot_fetched"

    async def _validate_readiness(self) -> None:
        assert self._inp is not None
        await workflow.execute_activity(
            validate_source_readiness,
            SourceReadinessInput(
                tenant_id=self._inp.tenant_id,
                global_asset_id=self._inp.global_asset_id,
                asset_binding_id=self._inp.asset_binding_id,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.phase = "source_ready"

    async def _compile_policy(self) -> None:
        assert self._inp is not None
        result = await workflow.execute_activity(
            compile_policy,
            PolicyCompileInput(
                tenant_id=self._inp.tenant_id,
                policy_template_id=self._inp.policy_template_id,
                pack_id=self._inp.pack_id,
                asset_binding_id=self._inp.asset_binding_id,
                idempotency_key=self._inp.idempotency_key,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.compiled_policy_id = result.policy_id
        self._state.phase = "policy_compiled"

        if result.lossy:
            # Lossy policy: request manual review and wait for ForceRepublish update
            self._state.manual_review.request(
                reason="lossy_policy",
                review_id=result.policy_id,
            )
            await workflow.wait_condition(lambda: self._force_republish_approved)
            self._state.manual_review.record_decision(
                decision="approved",
                reviewer_id="operator_via_force_republish",
            )

    async def _publish(self) -> None:
        assert self._inp is not None
        result = await workflow.execute_activity(
            publish_asset_offer,
            AssetPublishInput(
                tenant_id=self._inp.tenant_id,
                legal_entity_id=self._inp.legal_entity_id,
                asset_binding_id=self._inp.asset_binding_id,
                revision=self._inp.revision,
                global_asset_id=self._inp.global_asset_id,
                mapping_snapshot_id=self._state.mapping_snapshot_id,
                compiled_policy_id=self._state.compiled_policy_id,
                pack_id=self._inp.pack_id,
                idempotency_key=self._inp.idempotency_key,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.asset_offer_id = result.offer_id
        self._state.compensation.record("asset_offer_published", result.offer_id)
        self._state.phase = "published"

    async def _verify_visibility(self) -> None:
        assert self._inp is not None
        result = await workflow.execute_activity(
            run_consumer_visibility_check,
            VisibilityCheckInput(
                tenant_id=self._inp.tenant_id,
                offer_id=self._state.asset_offer_id,
                pack_id=self._inp.pack_id,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.discoverability_url = result.url
        self._state.phase = "visibility_verified"

    async def _record_evidence(self) -> None:
        assert self._inp is not None
        result = await workflow.execute_activity(
            record_publication_evidence,
            PublicationEvidenceInput(
                tenant_id=self._inp.tenant_id,
                legal_entity_id=self._inp.legal_entity_id,
                asset_binding_id=self._inp.asset_binding_id,
                revision=self._inp.revision,
                offer_id=self._state.asset_offer_id,
                discoverability_url=self._state.discoverability_url,
                idempotency_key=self._inp.idempotency_key,
            ),
            **RPC_OPTIONS,
        )
        self._state.evidence_ref = result.evidence_ref
        self._state.phase = "evidence_recorded"

    # ── Updates ───────────────────────────────────────────────────────────────

    @workflow.update
    async def force_republish(self, data: ForceRepublish) -> ForceRepublishResult:
        self._force_republish_approved = True
        self._state.manual_review.record_decision(
            decision="approved",
            reviewer_id=data.reviewer_id,
            notes=data.reason,
        )
        return ForceRepublishResult(accepted=True)

    @force_republish.validator
    def _validate_force_republish(self, data: ForceRepublish) -> None:
        # Only accept if the workflow is blocked on a lossy-policy review
        if not self._state.manual_review.is_pending:
            raise ApplicationError(
                "force_republish is only accepted while a manual review is pending.",
                type="INVALID_STATE",
                non_retryable=True,
            )

    # ── Query ─────────────────────────────────────────────────────────────────

    @workflow.query
    def get_status(self) -> PublishAssetStatusQuery:
        return PublishAssetStatusQuery(
            phase=self._state.phase,
            asset_offer_id=self._state.asset_offer_id,
            is_visible=bool(self._state.discoverability_url),
            blocking_reason=self._state.manual_review.blocking_reason,
        )
