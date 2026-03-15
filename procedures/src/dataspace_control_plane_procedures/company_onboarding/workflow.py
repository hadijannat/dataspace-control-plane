"""CompanyOnboardingWorkflow — durable Temporal entity workflow.

Orchestrates all phases of onboarding a legal entity into the dataspace:
  preflight → registration → approval → trust bootstrap →
  technical integration → compliance baseline → evidence emission.

Replay safety rules:
  - No datetime.now(), uuid4(), or random() calls in workflow code.
  - All I/O is delegated to activity functions.
  - Signals, Updates, and Queries only mutate/read local state.
"""
from __future__ import annotations

import asyncio
from typing import Any

from temporalio import workflow
from temporalio.exceptions import ApplicationError, CancelledError

from dataspace_control_plane_procedures._shared.search_attributes import (
    TENANT_ID,
    LEGAL_ENTITY_ID,
    PROCEDURE_TYPE,
    STATUS,
    build_search_attribute_updates,
)
from dataspace_control_plane_procedures._shared.activity_options import (
    PROVISIONING_OPTIONS,
    EXTERNAL_CALL_OPTIONS,
    RPC_OPTIONS,
)
from dataspace_control_plane_procedures._shared.continue_as_new import (
    CarryEnvelope,
    decode_start_input,
    should_continue_as_new,
)
from dataspace_control_plane_procedures._shared.versioning import patched

from .input import OnboardingStartInput, OnboardingResult, OnboardingCarryState
from .state import OnboardingWorkflowState
from .messages import (
    ExternalApprovalEvent,
    MissingInfoSubmitted,
    ApproveCaseInput,
    ApproveCaseResult,
    RejectCaseInput,
    RejectCaseResult,
)
from .activities import (
    preflight_validate,
    register_legal_entity,
    request_approval,
    bootstrap_wallet,
    bootstrap_connector,
    run_compliance_baseline,
    bind_hierarchy,
    emit_onboarding_evidence,
    PreflightInput,
    RegistrationInput,
    ApprovalRequestInput,
    WalletBootstrapInput,
    ConnectorBootstrapInput,
    ComplianceInput,
    HierarchyInput,
    EvidenceInput,
)
from .compensation import run_compensation
from .errors import PreflightValidationError, RegistrationRejectedError


@workflow.defn
class CompanyOnboardingWorkflow:
    """Entity workflow: one instance per legal entity, stable workflow ID.

    The workflow drives a company through the full dataspace onboarding
    lifecycle and emits a structured audit event on completion.
    """

    def __init__(self) -> None:
        self._state = OnboardingWorkflowState()
        self._approval_received: bool = False

    # ------------------------------------------------------------------
    # Main run method
    # ------------------------------------------------------------------

    @workflow.run
    async def run(
        self,
        inp: Any,
    ) -> OnboardingResult:
        start_input, carry = decode_start_input(
            inp,
            start_input_type=OnboardingStartInput,
            state_type=OnboardingCarryState,
        )
        if carry is not None:
            self._restore_from_carry(carry)

        # Publish search attributes so the workflow is discoverable.
        workflow.upsert_search_attributes(build_search_attribute_updates({
            TENANT_ID: start_input.tenant_id,
            LEGAL_ENTITY_ID: start_input.legal_entity_id,
            PROCEDURE_TYPE: "company-onboarding",
            STATUS: "running",
        }))

        try:
            if self._state.phase == "pending":
                await self._preflight(start_input)
                await self._checkpoint(start_input)

            if self._state.phase == "preflight_completed":
                await self._register(start_input)
                await self._checkpoint(start_input)

            if self._state.phase == "awaiting_approval":
                await self._await_approval()
                await self._checkpoint(start_input)

            if self._state.is_cancelled:
                raise ApplicationError("Onboarding cancelled before trust bootstrap")

            if self._state.phase == "approval_completed":
                await self._trust_bootstrap(start_input)
                await self._checkpoint(start_input)

            if self._state.phase == "trust_bootstrap_completed":
                await self._technical_integration(start_input)
                await self._checkpoint(start_input)

            if self._state.is_cancelled:
                raise ApplicationError("Onboarding cancelled after trust bootstrap")

            # v2 patch: run hierarchy binding when enabled.
            if patched("company_onboarding.v2_hierarchy_phase"):
                if self._state.phase == "technical_integration_completed":
                    await self._bind_hierarchy(start_input)
                    await self._checkpoint(start_input)
            elif self._state.phase == "technical_integration_completed":
                self._state.phase = "hierarchy_bound"

            if self._state.phase == "hierarchy_bound":
                await self._compliance_baseline(start_input)
                await self._checkpoint(start_input)

            if self._state.phase == "compliance_baseline_completed":
                await self._emit_evidence(start_input)

        except CancelledError:
            await run_compensation(self._state)
            raise
        except Exception:
            await run_compensation(self._state)
            raise

        workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "completed"}))
        await workflow.wait_condition(workflow.all_handlers_finished)

        return OnboardingResult(
            workflow_id=workflow.info().workflow_id,
            status="completed",
            registration_ref=self._state.registration_ref,
            bpnl=self._state.bpnl,
            wallet_did=self._state.wallet_ref,
            connector_binding_id=self._state.connector_ref,
            compliance_baseline_ref=self._state.compliance_ref,
        )

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    @workflow.signal
    async def external_approval_event(self, evt: ExternalApprovalEvent) -> None:
        """External approval callback from the MX portal or registry."""
        if self._state.dedupe.is_duplicate(evt.event_id):
            return
        self._state.dedupe.mark_handled(evt.event_id)

        if evt.approved:
            self._state.manual_review.record_decision(
                "approved",
                "external",
                evt.notes,
                decided_at=workflow.now(),
            )
        else:
            self._state.manual_review.record_decision(
                "rejected",
                "external",
                evt.notes,
                decided_at=workflow.now(),
            )

        self._approval_received = True

    @workflow.signal
    async def missing_info_submitted(self, evt: MissingInfoSubmitted) -> None:
        """Operator has provided missing information to unblock the review."""
        if self._state.dedupe.is_duplicate(evt.submission_id):
            return
        self._state.dedupe.mark_handled(evt.submission_id)

        # Re-open / advance the manual review state so the wait condition fires.
        self._state.manual_review.request(
            "waiting for additional info review",
            review_id=evt.submission_id,
            requested_at=workflow.now(),
        )

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------

    @workflow.update
    async def approve_case(self, cmd: ApproveCaseInput) -> ApproveCaseResult:
        """Internal reviewer approves the pending case."""
        self._state.manual_review.record_decision(
            "approved",
            cmd.reviewer_id,
            cmd.notes,
            decided_at=workflow.now(),
        )
        self._approval_received = True
        return ApproveCaseResult(
            accepted=True,
            review_id=self._state.manual_review.review_id,
        )

    @approve_case.validator
    def validate_approve_case(self, cmd: ApproveCaseInput) -> None:
        if not self._state.manual_review.is_pending:
            raise ApplicationError("No pending manual review to approve")

    @workflow.update
    async def reject_case(self, cmd: RejectCaseInput) -> RejectCaseResult:
        """Internal reviewer rejects the pending case."""
        self._state.manual_review.record_decision(
            "rejected",
            cmd.reviewer_id,
            cmd.reason,
            decided_at=workflow.now(),
        )
        self._state.is_cancelled = True
        self._approval_received = True
        return RejectCaseResult(accepted=True)

    @reject_case.validator
    def validate_reject_case(self, cmd: RejectCaseInput) -> None:
        if not self._state.manual_review.is_pending:
            raise ApplicationError("No pending manual review to reject")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @workflow.query
    def get_status(self):
        from .input import OnboardingStatusQuery

        return OnboardingStatusQuery(
            phase=self._state.phase,
            blocking_reason=self._state.manual_review.blocking_reason,
            external_refs={
                "registration_ref": self._state.registration_ref,
                "approval_ref": self._state.approval_ref,
                "wallet_ref": self._state.wallet_ref,
                "connector_ref": self._state.connector_ref,
            },
            next_required_action="approve" if self._state.manual_review.is_pending else "",
            is_complete=self._state.phase == "completed",
        )

    # ------------------------------------------------------------------
    # Internal phase helpers
    # ------------------------------------------------------------------

    def _restore_from_carry(self, carry: OnboardingCarryState) -> None:
        self._state.phase = carry.phase
        self._state.registration_ref = carry.registration_ref
        self._state.approval_ref = carry.approval_ref
        self._state.bpnl = carry.bpnl
        self._state.wallet_ref = carry.wallet_ref
        self._state.connector_ref = carry.connector_ref
        self._state.compliance_ref = carry.compliance_ref
        self._state.manual_review = self._state.manual_review.from_snapshot(carry.manual_review)
        self._state.compensation = self._state.compensation.from_snapshot(carry.compensation_markers)
        self._state.dedupe = self._state.dedupe.from_snapshot(carry.dedupe_ids)
        self._state.iteration = carry.iteration
        self._state.is_cancelled = carry.is_cancelled
        self._approval_received = self._state.manual_review.decision is not None

    async def _checkpoint(self, inp: OnboardingStartInput) -> None:
        """Continue-As-New if history is approaching the threshold."""
        info = workflow.info()
        if should_continue_as_new(info.get_current_history_length()):
            await workflow.wait_condition(workflow.all_handlers_finished)
            carry = OnboardingCarryState(
                phase=self._state.phase,
                registration_ref=self._state.registration_ref,
                approval_ref=self._state.approval_ref,
                bpnl=self._state.bpnl,
                wallet_ref=self._state.wallet_ref,
                connector_ref=self._state.connector_ref,
                compliance_ref=self._state.compliance_ref,
                dedupe_ids=self._state.dedupe.snapshot(),
                manual_review=self._state.manual_review.snapshot(),
                compensation_markers=self._state.compensation.snapshot(),
                is_cancelled=self._state.is_cancelled,
                iteration=self._state.iteration + 1,
            )
            workflow.continue_as_new(CarryEnvelope(start_input=inp, state=carry))

    async def _preflight(self, inp: OnboardingStartInput) -> None:
        self._state.phase = "preflight"
        result = await workflow.execute_activity(
            preflight_validate,
            PreflightInput(
                bpnl=inp.bpnl,
                jurisdiction=inp.jurisdiction,
                contact_email=inp.contact_email,
            ),
            **RPC_OPTIONS,
        )
        if not result.ok:
            raise PreflightValidationError(result.reason)
        self._state.phase = "preflight_completed"

    async def _register(self, inp: OnboardingStartInput) -> None:
        self._state.phase = "registration"

        reg_result = await workflow.execute_activity(
            register_legal_entity,
            RegistrationInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                legal_entity_name=inp.legal_entity_name,
                bpnl=inp.bpnl,
                jurisdiction=inp.jurisdiction,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.registration_ref = reg_result.registration_ref
        self._state.bpnl = reg_result.bpnl
        self._state.compensation.record("register_legal_entity", reg_result.registration_ref)

        self._state.phase = "awaiting_approval"
        approval_result = await workflow.execute_activity(
            request_approval,
            ApprovalRequestInput(
                tenant_id=inp.tenant_id,
                registration_ref=reg_result.registration_ref,
                contact_email=inp.contact_email,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.approval_ref = approval_result.approval_ref
        self._state.manual_review.request(
            "awaiting operator approval",
            approval_result.approval_ref,
            requested_at=workflow.now(),
        )

    async def _await_approval(self) -> None:
        if not self._approval_received and self._state.manual_review.decision is None:
            await workflow.wait_condition(lambda: self._approval_received)

        if self._state.manual_review.is_rejected or self._state.is_cancelled:
            raise RegistrationRejectedError("Onboarding rejected by reviewer")
        self._state.phase = "approval_completed"

    async def _trust_bootstrap(self, inp: OnboardingStartInput) -> None:
        self._state.phase = "trust_bootstrap"
        wallet_result = await workflow.execute_activity(
            bootstrap_wallet,
            WalletBootstrapInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                bpnl=inp.bpnl,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.wallet_ref = wallet_result.wallet_ref
        self._state.phase = "trust_bootstrap_completed"

    async def _technical_integration(self, inp: OnboardingStartInput) -> None:
        self._state.phase = "technical_integration"
        connector_result = await workflow.execute_activity(
            bootstrap_connector,
            ConnectorBootstrapInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                connector_url=inp.connector_url,
                wallet_ref=self._state.wallet_ref,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.connector_ref = connector_result.connector_binding_id
        self._state.phase = "technical_integration_completed"

    async def _bind_hierarchy(self, inp: OnboardingStartInput) -> None:
        """v2 patch: bind entity into the parent/child BPNL topology."""
        self._state.phase = "hierarchy_binding"
        await workflow.execute_activity(
            bind_hierarchy,
            HierarchyInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
            ),
            **RPC_OPTIONS,
        )
        self._state.phase = "hierarchy_bound"

    async def _compliance_baseline(self, inp: OnboardingStartInput) -> None:
        self._state.phase = "compliance_baseline"
        result = await workflow.execute_activity(
            run_compliance_baseline,
            ComplianceInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.compliance_ref = result.baseline_ref
        self._state.phase = "compliance_baseline_completed"

    async def _emit_evidence(self, inp: OnboardingStartInput) -> None:
        await workflow.execute_activity(
            emit_onboarding_evidence,
            EvidenceInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                registration_ref=self._state.registration_ref,
                bpnl=self._state.bpnl,
                workflow_id=workflow.info().workflow_id,
            ),
            **RPC_OPTIONS,
        )
        self._state.phase = "completed"
