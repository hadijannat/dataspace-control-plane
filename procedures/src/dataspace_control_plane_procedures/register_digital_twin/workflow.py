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

from .input import TwinStartInput, TwinResult, TwinStatusQuery
from .state import TwinWorkflowState
from .messages import ApproveSemanticMapping, SemanticApprovalResult
from .activities import (
    validate_canonical_shell, ShellValidateInput,
    upsert_aas_shell, ShellUpsertInput,
    upsert_submodels, SubmodelUpsertInput,
    register_descriptor_in_registry, RegistryRegInput,
    bind_access_rules, AccessRuleInput,
    verify_readback_from_registry, VerifyReadbackInput,
    record_twin_evidence, TwinEvidenceInput,
    deregister_shell,
)
from .compensation import run_twin_compensation
from .errors import ShellValidationError, TwinRegistrationError


@workflow.defn
class RegisterDigitalTwinWorkflow:
    def __init__(self) -> None:
        self._state = TwinWorkflowState()
        self._review_decided: bool = False

    @workflow.run
    async def run(self, inp: TwinStartInput) -> TwinResult:
        workflow.upsert_search_attributes(build_search_attribute_updates({
            TENANT_ID: inp.tenant_id,
            LEGAL_ENTITY_ID: inp.legal_entity_id,
            PROCEDURE_TYPE: "register-digital-twin",
            STATUS: "running",
            ASSET_ID: inp.global_asset_id,
        }))
        try:
            await self._validate_shell(inp)
            if self._state.manual_review.is_pending:
                await workflow.wait_condition(lambda: self._review_decided)
                if self._state.manual_review.is_rejected:
                    raise TwinRegistrationError("Semantic mapping review rejected")
            await self._upsert_shell(inp)
            await self._upsert_submodels(inp)
            await self._register_descriptor(inp)
            await self._bind_access_rules(inp)
            await self._verify_readback(inp)
            await self._record_evidence(inp)
        except (CancelledError, Exception):
            await run_twin_compensation(self._state, inp.tenant_id)
            raise

        workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "completed"}))
        await workflow.wait_condition(workflow.all_handlers_finished)
        return TwinResult(
            workflow_id=workflow.info().workflow_id,
            status="completed",
            shell_id=self._state.shell_id,
            registry_url=self._state.registry_url,
            evidence_ref=self._state.evidence_ref,
        )

    @workflow.update
    async def approve_semantic_mapping(self, cmd: ApproveSemanticMapping) -> SemanticApprovalResult:
        self._state.manual_review.record_decision(
            "approved",
            cmd.reviewer_id,
            f"confirmed: {cmd.confirmed_semantic_id}",
            decided_at=workflow.now(),
        )
        self._review_decided = True
        return SemanticApprovalResult(accepted=True)

    @approve_semantic_mapping.validator
    def validate_approve_semantic_mapping(self, cmd: ApproveSemanticMapping) -> None:
        if not self._state.manual_review.is_pending:
            raise ApplicationError("No pending semantic mapping review")

    @workflow.query
    def get_status(self) -> TwinStatusQuery:
        return TwinStatusQuery(
            phase=self._state.phase,
            shell_id=self._state.shell_id,
            submodel_count=len(self._state.submodel_ids),
            registry_registered=bool(self._state.registry_url),
            access_bound=bool(self._state.access_rule_ids),
            blocking_reason=self._state.manual_review.blocking_reason,
        )

    async def _validate_shell(self, inp: TwinStartInput) -> None:
        self._state.phase = "validating"
        result = await workflow.execute_activity(
            validate_canonical_shell,
            ShellValidateInput(
                tenant_id=inp.tenant_id,
                aas_id=inp.aas_id,
                shell_descriptor=inp.shell_descriptor,
                submodel_refs=inp.submodel_refs,
                semantic_id=inp.semantic_id,
                pack_id=inp.pack_id,
            ),
            **RPC_OPTIONS,
        )
        if not result.ok:
            raise ShellValidationError(f"Shell validation failed: {result.warnings}")
        if result.requires_review:
            self._state.manual_review.request(
                f"Ambiguous semantic ID: {result.ambiguous_semantic_id}",
                review_id=inp.aas_id,
                requested_at=workflow.now(),
            )
        self._state.phase = "validated"

    async def _upsert_shell(self, inp: TwinStartInput) -> None:
        result = await workflow.execute_activity(
            upsert_aas_shell,
            ShellUpsertInput(
                tenant_id=inp.tenant_id,
                aas_id=inp.aas_id,
                shell_descriptor=inp.shell_descriptor,
                pack_id=inp.pack_id,
                idempotency_key=f"{inp.aas_id}:{inp.revision}",
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.shell_id = result.shell_id
        self._state.compensation.record("upsert_aas_shell", result.shell_id)
        self._state.phase = "shell_upserted"

    async def _upsert_submodels(self, inp: TwinStartInput) -> None:
        result = await workflow.execute_activity(
            upsert_submodels,
            SubmodelUpsertInput(
                tenant_id=inp.tenant_id,
                shell_id=self._state.shell_id,
                submodel_refs=inp.submodel_refs,
                pack_id=inp.pack_id,
                idempotency_key=f"{inp.aas_id}:{inp.revision}:submodels",
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.submodel_ids = result.submodel_ids
        self._state.phase = "submodels_upserted"

    async def _register_descriptor(self, inp: TwinStartInput) -> None:
        result = await workflow.execute_activity(
            register_descriptor_in_registry,
            RegistryRegInput(
                tenant_id=inp.tenant_id,
                shell_id=self._state.shell_id,
                aas_id=inp.aas_id,
                global_asset_id=inp.global_asset_id,
                submodel_ids=list(self._state.submodel_ids),
                pack_id=inp.pack_id,
                idempotency_key=f"{inp.aas_id}:{inp.revision}:registry",
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.registry_url = result.registry_url
        self._state.phase = "registry_registered"

    async def _bind_access_rules(self, inp: TwinStartInput) -> None:
        result = await workflow.execute_activity(
            bind_access_rules,
            AccessRuleInput(
                tenant_id=inp.tenant_id,
                shell_id=self._state.shell_id,
                legal_entity_id=inp.legal_entity_id,
                pack_id=inp.pack_id,
                idempotency_key=f"{inp.aas_id}:{inp.revision}:access",
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.access_rule_ids = result.rule_ids
        self._state.phase = "access_bound"

    async def _verify_readback(self, inp: TwinStartInput) -> None:
        result = await workflow.execute_activity(
            verify_readback_from_registry,
            VerifyReadbackInput(
                tenant_id=inp.tenant_id,
                shell_id=self._state.shell_id,
                aas_registry_url=self._state.registry_url,
                pack_id=inp.pack_id,
            ),
            **RPC_OPTIONS,
        )
        if not result.ok:
            raise TwinRegistrationError("Registry readback verification failed")
        self._state.phase = "verification_passed"

    async def _record_evidence(self, inp: TwinStartInput) -> None:
        result = await workflow.execute_activity(
            record_twin_evidence,
            TwinEvidenceInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                aas_id=inp.aas_id,
                shell_id=self._state.shell_id,
                registry_url=self._state.registry_url,
                idempotency_key=f"{inp.aas_id}:{inp.revision}:evidence",
            ),
            **RPC_OPTIONS,
        )
        self._state.evidence_ref = result.evidence_ref
