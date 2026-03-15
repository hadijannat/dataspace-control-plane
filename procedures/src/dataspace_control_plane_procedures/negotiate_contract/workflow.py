"""NegotiateContractWorkflow — durable Temporal entity workflow.

Orchestrates DSP contract negotiation:
  preflight → credentials_checked → negotiation_started → awaiting_counterparty
  → [manual_review?] → agreement_concluded → transfer_authorized.

Replay safety rules:
  - No datetime.now(), uuid4(), or random() calls in workflow code.
  - All I/O is delegated to activity functions.
  - Signals, Updates, and Queries only mutate/read local state.
"""
from __future__ import annotations

from temporalio import workflow
from temporalio.exceptions import ApplicationError, CancelledError

from dataspace_control_plane_procedures._shared.search_attributes import (
    TENANT_ID,
    LEGAL_ENTITY_ID,
    PROCEDURE_TYPE,
    STATUS,
    AGREEMENT_ID,
    ASSET_ID,
)
from dataspace_control_plane_procedures._shared.activity_options import (
    PROVISIONING_OPTIONS,
    EXTERNAL_CALL_OPTIONS,
    RPC_OPTIONS,
)
from dataspace_control_plane_procedures._shared.continue_as_new import should_continue_as_new

from .input import NegotiationStartInput, NegotiationResult, NegotiationCarryState
from .state import NegotiationWorkflowState
from .messages import (
    CounterpartyAccepted,
    CounterpartyRejected,
    CounterpartyCounteroffer,
    NegotiationExpired,
    AcceptCounteroffer,
    CounterOfferResult,
    RejectNegotiation,
    RejectionResult,
)
from .activities import (
    check_credentials_and_offer,
    start_dsp_negotiation,
    submit_counteroffer,
    conclude_agreement,
    create_entitlement,
    issue_transfer_authorization,
    record_negotiation_evidence,
    CredCheckInput,
    DspNegotiationInput,
    CounterOfferInput,
    AgreementInput,
    EntitlementInput,
    TransferAuthInput,
    EvidenceInput,
)
from .compensation import run_negotiation_compensation
from .errors import (
    CredentialCheckError,
    CounterpartyRejectedError,
    AgreementError,
)


@workflow.defn
class NegotiateContractWorkflow:
    """Entity workflow: one instance per offer/counterparty/purpose.

    Drives DSP contract negotiation through the full lifecycle and emits
    a structured audit record on completion.
    """

    def __init__(self) -> None:
        self._state = NegotiationWorkflowState()
        # Track current offer_id — may change across counteroffer rounds.
        self._current_offer_id: str = ""

    # ------------------------------------------------------------------
    # Main run method
    # ------------------------------------------------------------------

    @workflow.run
    async def run(self, inp: NegotiationStartInput) -> NegotiationResult:
        self._current_offer_id = inp.offer_id

        workflow.upsert_search_attributes({
            TENANT_ID: inp.tenant_id,
            LEGAL_ENTITY_ID: inp.legal_entity_id,
            PROCEDURE_TYPE: "negotiate-contract",
            STATUS: "running",
            ASSET_ID: inp.asset_id,
            AGREEMENT_ID: "",
        })

        try:
            # Check continue-as-new at workflow entry (carry state re-entry).
            await self._check_continue_as_new(inp)

            await self._check_credentials(inp)
            await self._start_negotiation(inp)
            await self._await_counterparty_response(inp)
            await self._conclude_agreement(inp)
            await self._create_entitlement(inp)
            await self._issue_transfer_auth(inp)
            await self._record_evidence(inp, outcome="completed")

        except CancelledError:
            await run_negotiation_compensation(self._state)
            raise
        except Exception:
            await run_negotiation_compensation(self._state)
            await self._record_evidence(inp, outcome="failed")
            raise

        workflow.upsert_search_attributes({
            STATUS: "completed",
            AGREEMENT_ID: self._state.agreement_id,
        })
        await workflow.wait_condition(workflow.all_handlers_finished)

        return NegotiationResult(
            workflow_id=workflow.info().workflow_id,
            status="completed",
            agreement_id=self._state.agreement_id,
            entitlement_id=self._state.entitlement_id,
            transfer_auth_token=self._state.transfer_auth_token,
        )

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    @workflow.signal
    async def counterparty_accepted(self, evt: CounterpartyAccepted) -> None:
        """Async callback from connector webhook — counterparty accepted."""
        if self._state.dedupe.is_duplicate(evt.event_id):
            return
        self._state.dedupe.mark_handled(evt.event_id)
        self._state.counterparty_response = "accepted"

    @workflow.signal
    async def counterparty_rejected(self, evt: CounterpartyRejected) -> None:
        """Async callback from connector webhook — counterparty rejected."""
        if self._state.dedupe.is_duplicate(evt.event_id):
            return
        self._state.dedupe.mark_handled(evt.event_id)
        self._state.counterparty_response = "rejected"

    @workflow.signal
    async def counterparty_counteroffer(self, evt: CounterpartyCounteroffer) -> None:
        """Async callback from connector webhook — counterparty sent counteroffer."""
        if self._state.dedupe.is_duplicate(evt.event_id):
            return
        self._state.dedupe.mark_handled(evt.event_id)
        self._state.pending_counteroffer_offer_id = evt.new_offer_id
        self._state.pending_counteroffer_policy_id = evt.policy_id
        self._state.counterparty_response = "counteroffer"

    @workflow.signal
    async def negotiation_expired(self, evt: NegotiationExpired) -> None:
        """Timeout signal from external scheduler."""
        if self._state.dedupe.is_duplicate(evt.event_id):
            return
        self._state.dedupe.mark_handled(evt.event_id)
        self._state.is_expired = True

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------

    @workflow.update
    async def accept_counteroffer(self, cmd: AcceptCounteroffer) -> CounterOfferResult:
        """Human reviewer accepts the pending counteroffer."""
        self._state.manual_review.record_decision("approved", cmd.reviewer_id)
        self._current_offer_id = cmd.new_offer_id
        return CounterOfferResult(accepted=True)

    @accept_counteroffer.validator
    def validate_accept_counteroffer(self, cmd: AcceptCounteroffer) -> None:
        if self._state.counterparty_response != "counteroffer":
            raise ApplicationError("No pending counteroffer to accept")

    @workflow.update
    async def reject_negotiation(self, cmd: RejectNegotiation) -> RejectionResult:
        """Human reviewer rejects the negotiation."""
        self._state.manual_review.record_decision("rejected", cmd.reviewer_id, cmd.reason)
        self._state.negotiation_state = "failed"
        return RejectionResult(accepted=True)

    @reject_negotiation.validator
    def validate_reject_negotiation(self, cmd: RejectNegotiation) -> None:
        if self._state.negotiation_state in ("agreement_concluded", "transfer_authorized", "expired", "failed"):
            raise ApplicationError(
                f"Cannot reject negotiation in state '{self._state.negotiation_state}'"
            )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @workflow.query
    def get_status(self):
        from .input import NegotiationStatusQuery

        return NegotiationStatusQuery(
            negotiation_state=self._state.negotiation_state,
            offer_id=self._current_offer_id,
            agreement_id=self._state.agreement_id,
            blocking_reason=self._state.manual_review.blocking_reason,
            next_action="review_counteroffer" if self._state.counterparty_response == "counteroffer"
                        and not self._state.manual_review.decision else "",
            is_concluded=self._state.negotiation_state in ("agreement_concluded", "transfer_authorized"),
        )

    # ------------------------------------------------------------------
    # Internal phase helpers
    # ------------------------------------------------------------------

    async def _check_continue_as_new(self, inp: NegotiationStartInput) -> None:
        info = workflow.info()
        if should_continue_as_new(info.get_current_history_length()):
            carry = NegotiationCarryState(
                negotiation_state=self._state.negotiation_state,
                negotiation_ref=self._state.negotiation_ref,
                agreement_id=self._state.agreement_id,
                entitlement_id=self._state.entitlement_id,
                dedupe_ids=self._state.dedupe.snapshot(),
                iteration=self._state.iteration + 1,
            )
            workflow.continue_as_new(carry)

    async def _check_credentials(self, inp: NegotiationStartInput) -> None:
        self._state.negotiation_state = "preflight"
        result = await workflow.execute_activity(
            check_credentials_and_offer,
            CredCheckInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                offer_id=inp.offer_id,
                policy_template_id=inp.policy_template_id,
                counterparty_connector_id=inp.counterparty_connector_id,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        if not result.ok:
            raise CredentialCheckError(result.reason)
        self._state.negotiation_state = "credentials_checked"

    async def _start_negotiation(self, inp: NegotiationStartInput) -> None:
        result = await workflow.execute_activity(
            start_dsp_negotiation,
            DspNegotiationInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                offer_id=self._current_offer_id,
                counterparty_connector_id=inp.counterparty_connector_id,
                purpose=inp.purpose,
                policy_template_id=inp.policy_template_id,
                pack_id=inp.pack_id,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.negotiation_ref = result.negotiation_ref
        self._state.compensation.record("start_dsp_negotiation", result.negotiation_ref)
        self._state.negotiation_state = "negotiation_started"

    async def _await_counterparty_response(self, inp: NegotiationStartInput) -> None:
        """Wait for counterparty response, handling expiry, rejection, and counteroffer loops."""
        while True:
            # Reset response so we wait cleanly on each iteration.
            self._state.counterparty_response = None
            self._state.negotiation_state = "awaiting_counterparty"

            await workflow.wait_condition(
                lambda: self._state.counterparty_response is not None or self._state.is_expired
            )

            if self._state.is_expired:
                self._state.negotiation_state = "expired"
                raise ApplicationError("Negotiation expired before counterparty responded")

            if self._state.counterparty_response == "rejected":
                self._state.negotiation_state = "failed"
                raise CounterpartyRejectedError("Counterparty rejected the offer")

            if self._state.counterparty_response == "counteroffer":
                self._state.negotiation_state = "manual_review"
                self._state.manual_review.request(
                    "counterparty sent counteroffer — awaiting reviewer decision",
                    review_id=self._state.pending_counteroffer_offer_id,
                )

                # Wait for human to accept or reject via Update.
                await workflow.wait_condition(
                    lambda: self._state.manual_review.decision is not None
                )

                if self._state.manual_review.is_rejected or self._state.negotiation_state == "failed":
                    raise CounterpartyRejectedError("Reviewer rejected the counteroffer negotiation")

                # Submit the accepted counteroffer and re-enter wait loop.
                co_result = await workflow.execute_activity(
                    submit_counteroffer,
                    CounterOfferInput(
                        tenant_id=inp.tenant_id,
                        negotiation_ref=self._state.negotiation_ref,
                        new_offer_id=self._state.pending_counteroffer_offer_id,
                        policy_id=self._state.pending_counteroffer_policy_id,
                    ),
                    **EXTERNAL_CALL_OPTIONS,
                )
                if co_result.new_negotiation_ref:
                    self._state.negotiation_ref = co_result.new_negotiation_ref

                # Reset manual_review decision for next round.
                self._state.manual_review.decision = None
                self._state.manual_review.is_pending = False
                continue

            # Response is "accepted" — exit loop.
            break

    async def _conclude_agreement(self, inp: NegotiationStartInput) -> None:
        result = await workflow.execute_activity(
            conclude_agreement,
            AgreementInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                negotiation_ref=self._state.negotiation_ref,
                offer_id=self._current_offer_id,
                asset_id=inp.asset_id,
                counterparty_connector_id=inp.counterparty_connector_id,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.agreement_id = result.agreement_id
        self._state.negotiation_state = "agreement_concluded"
        workflow.upsert_search_attributes({AGREEMENT_ID: self._state.agreement_id})

    async def _create_entitlement(self, inp: NegotiationStartInput) -> None:
        result = await workflow.execute_activity(
            create_entitlement,
            EntitlementInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                agreement_id=self._state.agreement_id,
                asset_id=inp.asset_id,
                purpose=inp.purpose,
            ),
            **RPC_OPTIONS,
        )
        self._state.entitlement_id = result.entitlement_id

    async def _issue_transfer_auth(self, inp: NegotiationStartInput) -> None:
        result = await workflow.execute_activity(
            issue_transfer_authorization,
            TransferAuthInput(
                tenant_id=inp.tenant_id,
                agreement_id=self._state.agreement_id,
                entitlement_id=self._state.entitlement_id,
                asset_id=inp.asset_id,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.transfer_auth_token = result.transfer_auth_token
        self._state.negotiation_state = "transfer_authorized"

    async def _record_evidence(self, inp: NegotiationStartInput, outcome: str) -> None:
        await workflow.execute_activity(
            record_negotiation_evidence,
            EvidenceInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                negotiation_ref=self._state.negotiation_ref,
                agreement_id=self._state.agreement_id,
                workflow_id=workflow.info().workflow_id,
                outcome=outcome,
            ),
            **RPC_OPTIONS,
        )
