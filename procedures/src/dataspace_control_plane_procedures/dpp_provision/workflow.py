from __future__ import annotations

from temporalio import workflow
from temporalio.exceptions import ApplicationError, CancelledError

from dataspace_control_plane_procedures._shared.search_attributes import (
    TENANT_ID, LEGAL_ENTITY_ID, PROCEDURE_TYPE, STATUS, ASSET_ID,
    build_search_attribute_updates,
)
from dataspace_control_plane_procedures._shared.activity_options import (
    PROVISIONING_OPTIONS, EXTERNAL_CALL_OPTIONS, RPC_OPTIONS,
)

from .input import DppStartInput, DppResult, DppStatusQuery
from .state import DppWorkflowState
from .messages import ApproveMandatoryFieldsReview, ApproveResult
from .activities import (
    collect_source_snapshot, SourceSnapshotInput,
    resolve_submodel_templates, TemplateResolveInput,
    compile_submodels, SubmodelCompileInput,
    upsert_dpp_twin_data, DppUpsertInput,
    bind_identifier_link, IdLinkInput,
    record_dpp_evidence, DppEvidenceInput,
    deregister_dpp,
)
from .compensation import run_dpp_compensation
from .errors import DppProvisionError


@workflow.defn
class DppProvisionWorkflow:
    def __init__(self) -> None:
        self._state = DppWorkflowState()
        self._review_decided: bool = False

    @workflow.run
    async def run(self, inp: DppStartInput) -> DppResult:
        workflow.upsert_search_attributes(build_search_attribute_updates({
            TENANT_ID: inp.tenant_id,
            LEGAL_ENTITY_ID: inp.legal_entity_id,
            PROCEDURE_TYPE: "dpp-provision",
            STATUS: "running",
            ASSET_ID: inp.asset_id,
        }))
        try:
            await self._collect_source_snapshot(inp)
            template_refs = await self._resolve_submodel_templates(inp)
            await self._compile_submodels(inp, template_refs)
            if self._state.missing_mandatory:
                self._state.manual_review.request(
                    f"Missing mandatory fields: {', '.join(self._state.missing_mandatory)}",
                    review_id=inp.product_instance_id,
                    requested_at=workflow.now(),
                )
                await workflow.wait_condition(lambda: self._review_decided)
                if self._state.manual_review.is_rejected:
                    raise DppProvisionError("Mandatory fields review rejected")
            await self._upsert_dpp_twin_data(inp)
            await self._bind_identifier_link(inp)
            await self._record_dpp_evidence(inp)
        except (CancelledError, Exception):
            await run_dpp_compensation(self._state)
            raise

        workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "completed"}))
        await workflow.wait_condition(workflow.all_handlers_finished)
        return DppResult(
            workflow_id=workflow.info().workflow_id,
            status="completed",
            dpp_id=self._state.dpp_id,
            identifier_link=self._state.identifier_link,
            evidence_ref=self._state.evidence_ref,
        )

    @workflow.update
    async def approve_mandatory_fields_review(
        self, cmd: ApproveMandatoryFieldsReview
    ) -> ApproveResult:
        self._state.field_overrides.update(cmd.field_overrides)
        self._state.manual_review.record_decision(
            "approved",
            cmd.reviewer_id,
            f"field_overrides: {list(cmd.field_overrides.keys())}",
            decided_at=workflow.now(),
        )
        self._review_decided = True
        return ApproveResult(accepted=True)

    @approve_mandatory_fields_review.validator
    def validate_approve_mandatory_fields_review(
        self, cmd: ApproveMandatoryFieldsReview
    ) -> None:
        if not self._state.manual_review.is_pending:
            raise ApplicationError("No pending mandatory fields review")

    @workflow.query
    def get_status(self) -> DppStatusQuery:
        return DppStatusQuery(
            phase=self._state.phase,
            dpp_id=self._state.dpp_id,
            completeness_score=self._state.completeness_score,
            is_published=bool(self._state.identifier_link),
            blocking_reason=self._state.manual_review.blocking_reason,
        )

    async def _collect_source_snapshot(self, inp: DppStartInput) -> None:
        self._state.phase = "source_snapshot_taken"
        result = await workflow.execute_activity(
            collect_source_snapshot,
            SourceSnapshotInput(
                tenant_id=inp.tenant_id,
                product_instance_id=inp.product_instance_id,
                source_system_ref=inp.source_system_ref,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.source_snapshot_ref = result.snapshot_ref

    async def _resolve_submodel_templates(self, inp: DppStartInput) -> list[str]:
        result = await workflow.execute_activity(
            resolve_submodel_templates,
            TemplateResolveInput(
                tenant_id=inp.tenant_id,
                submodel_template_ids=inp.submodel_template_ids,
                pack_id=inp.pack_id,
            ),
            **RPC_OPTIONS,
        )
        return result.template_refs

    async def _compile_submodels(self, inp: DppStartInput, template_refs: list[str]) -> None:
        result = await workflow.execute_activity(
            compile_submodels,
            SubmodelCompileInput(
                tenant_id=inp.tenant_id,
                product_instance_id=inp.product_instance_id,
                snapshot_ref=self._state.source_snapshot_ref,
                template_refs=template_refs,
                field_overrides=dict(self._state.field_overrides),
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.submodel_ids = result.submodel_ids
        self._state.completeness_score = result.completeness_score
        self._state.missing_mandatory = list(result.missing_mandatory)
        self._state.phase = "submodels_compiled"

    async def _upsert_dpp_twin_data(self, inp: DppStartInput) -> None:
        result = await workflow.execute_activity(
            upsert_dpp_twin_data,
            DppUpsertInput(
                tenant_id=inp.tenant_id,
                product_instance_id=inp.product_instance_id,
                revision=inp.revision,
                submodel_ids=list(self._state.submodel_ids),
                asset_id=inp.asset_id,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.dpp_id = result.dpp_id
        self._state.compensation.record("upsert_dpp_twin_data", result.dpp_id)
        self._state.phase = "passport_registered"

    async def _bind_identifier_link(self, inp: DppStartInput) -> None:
        result = await workflow.execute_activity(
            bind_identifier_link,
            IdLinkInput(
                tenant_id=inp.tenant_id,
                dpp_id=self._state.dpp_id,
                product_instance_id=inp.product_instance_id,
                pack_id=inp.pack_id,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.identifier_link = result.identifier_link
        self._state.phase = "id_link_bound"

    async def _record_dpp_evidence(self, inp: DppStartInput) -> None:
        result = await workflow.execute_activity(
            record_dpp_evidence,
            DppEvidenceInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                dpp_id=self._state.dpp_id,
                identifier_link=self._state.identifier_link,
                workflow_id=workflow.info().workflow_id,
                product_instance_id=inp.product_instance_id,
            ),
            **RPC_OPTIONS,
        )
        self._state.evidence_ref = result.evidence_ref
        self._state.phase = "evidence_recorded"
