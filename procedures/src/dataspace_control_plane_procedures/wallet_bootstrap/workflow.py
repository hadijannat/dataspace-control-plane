from __future__ import annotations

import asyncio

from temporalio import workflow
from temporalio.exceptions import ApplicationError

from .._shared.activity_options import (
    PROVISIONING_OPTIONS,
    EXTERNAL_CALL_OPTIONS,
    RPC_OPTIONS,
)
from .._shared.search_attributes import (
    TENANT_ID,
    LEGAL_ENTITY_ID,
    PROCEDURE_TYPE,
    STATUS,
    build_search_attribute_updates,
)
from .input import (
    WalletStartInput,
    WalletResult,
    WalletStatusQuery,
    WalletCarryState,
)
from .state import WalletWorkflowState
from .messages import (
    CredentialIssuanceCallback,
    ReissueRequested,
    PauseWallet,
    PauseResult,
    ResumeWallet,
    ResumeResult,
)
from .activities import (
    create_wallet,
    register_did,
    setup_verification_methods,
    request_credential_from_issuer,
    verify_credential_presentation,
    bind_wallet_to_connector,
    CreateWalletInput,
    RegisterDidInput,
    VerifMethodInput,
    CredReqInput,
    PresVerifyInput,
    WalletBindInput,
)
from .compensation import (
    run_wallet_compensation,
)
from .manifest import MANIFEST

_TERMINAL_STATES = frozenset({"bound_to_connector", "failed"})
_PAUSED_STATE = "paused"


@workflow.defn
class WalletBootstrapWorkflow:
    """Entity workflow: DCP wallet creation, DID registration, credential, connector binding."""

    def __init__(self) -> None:
        self._state = WalletWorkflowState()
        self._inp: WalletStartInput | None = None
        self._credential_received: bool = False
        self._reissue_requested: bool = False
        self._reissue_type: str = ""
        self._paused: bool = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @workflow.run
    async def run(self, inp: WalletStartInput) -> WalletResult:
        self._inp = inp

        workflow.upsert_search_attributes(build_search_attribute_updates({
            TENANT_ID: inp.tenant_id,
            LEGAL_ENTITY_ID: inp.legal_entity_id,
            PROCEDURE_TYPE: MANIFEST.workflow_type,
            STATUS: "running",
        }))

        try:
            await self._create_wallet()
            await self._register_did()
            await self._setup_verification_methods()
            await self._request_credential()
            await self._await_issuance()
            await self._verify_presentation()
            await self._bind_to_connector()
        except Exception as exc:
            workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "failed"}))
            await run_wallet_compensation(self._state, inp.tenant_id)
            raise

        workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "completed"}))

        await workflow.wait_condition(workflow.all_handlers_finished)

        return WalletResult(
            workflow_id=workflow.info().workflow_id,
            status="completed",
            wallet_ref=self._state.wallet_ref,
            wallet_did=self._state.wallet_did,
            credential_ids=list(self._state.credential_ids),
        )

    # ── Steps ─────────────────────────────────────────────────────────────────

    async def _create_wallet(self) -> None:
        assert self._inp is not None
        result = await workflow.execute_activity(
            create_wallet,
            CreateWalletInput(
                tenant_id=self._inp.tenant_id,
                legal_entity_id=self._inp.legal_entity_id,
                bpnl=self._inp.bpnl,
                wallet_profile=self._inp.wallet_profile,
                trust_anchor_url=self._inp.trust_anchor_url,
                idempotency_key=self._inp.idempotency_key,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.wallet_ref = result.wallet_ref
        self._state.compensation.record("wallet_created", result.wallet_ref)
        self._state.wallet_state = "did_ready"

    async def _register_did(self) -> None:
        assert self._inp is not None
        result = await workflow.execute_activity(
            register_did,
            RegisterDidInput(
                tenant_id=self._inp.tenant_id,
                wallet_ref=self._state.wallet_ref,
                trust_anchor_url=self._inp.trust_anchor_url,
                idempotency_key=self._inp.idempotency_key,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.wallet_did = result.did
        self._state.wallet_state = "did_ready"

    async def _setup_verification_methods(self) -> None:
        assert self._inp is not None
        await workflow.execute_activity(
            setup_verification_methods,
            VerifMethodInput(
                tenant_id=self._inp.tenant_id,
                wallet_ref=self._state.wallet_ref,
                wallet_did=self._state.wallet_did,
                idempotency_key=self._inp.idempotency_key,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.wallet_state = "verification_methods_ready"

    async def _request_credential(self) -> None:
        assert self._inp is not None
        result = await workflow.execute_activity(
            request_credential_from_issuer,
            CredReqInput(
                tenant_id=self._inp.tenant_id,
                wallet_ref=self._state.wallet_ref,
                wallet_did=self._state.wallet_did,
                issuer_endpoint=self._state.issuer_endpoint,
                idempotency_key=self._inp.idempotency_key,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.wallet_state = "credential_request_sent"

    async def _await_issuance(self) -> None:
        """Block until CredentialIssuanceCallback signal sets _credential_received."""
        await workflow.wait_condition(lambda: self._credential_received)
        self._state.wallet_state = "credential_issued"

    async def _verify_presentation(self) -> None:
        assert self._inp is not None
        result = await workflow.execute_activity(
            verify_credential_presentation,
            PresVerifyInput(
                tenant_id=self._inp.tenant_id,
                wallet_ref=self._state.wallet_ref,
                wallet_did=self._state.wallet_did,
                credential_ids=list(self._state.credential_ids),
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        if not result.ok:
            # Request manual review and wait for a resume
            self._state.manual_review.request(
                reason="presentation_verification_failed",
                review_id=result.verification_report_ref,
                requested_at=workflow.now(),
            )
            self._paused = True
            await workflow.wait_condition(lambda: not self._paused)
        self._state.wallet_state = "presentation_verified"

    async def _bind_to_connector(self) -> None:
        assert self._inp is not None
        result = await workflow.execute_activity(
            bind_wallet_to_connector,
            WalletBindInput(
                tenant_id=self._inp.tenant_id,
                wallet_ref=self._state.wallet_ref,
                wallet_did=self._state.wallet_did,
                legal_entity_id=self._inp.legal_entity_id,
                idempotency_key=self._inp.idempotency_key,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.is_bound_to_connector = True
        self._state.wallet_state = "bound_to_connector"

    # ── Signals ───────────────────────────────────────────────────────────────

    @workflow.signal
    async def credential_issuance_callback(self, data: CredentialIssuanceCallback) -> None:
        """Async callback from issuer; deduplicated by event_id."""
        if self._state.dedupe.is_duplicate(data.event_id):
            return
        self._state.dedupe.mark_handled(data.event_id)
        if data.credential_id not in self._state.credential_ids:
            self._state.credential_ids.append(data.credential_id)
        self._credential_received = True

    @workflow.signal
    async def reissue_requested(self, data: ReissueRequested) -> None:
        """Queue a credential reissue; deduplicated by event_id."""
        if self._state.dedupe.is_duplicate(data.event_id):
            return
        self._state.dedupe.mark_handled(data.event_id)
        self._reissue_requested = True
        self._reissue_type = data.credential_type
        # Re-enter manual review so an operator can confirm
        self._state.manual_review.request(
            reason=f"reissue_requested:{data.reason}",
            review_id=data.event_id,
            requested_at=workflow.now(),
        )

    # ── Updates ───────────────────────────────────────────────────────────────

    @workflow.update
    async def pause_wallet(self, data: PauseWallet) -> PauseResult:
        self._paused = True
        self._state.manual_review.request(
            reason="operator_pause",
            review_id=data.reviewer_id,
            requested_at=workflow.now(),
        )
        return PauseResult(accepted=True)

    @pause_wallet.validator
    def _validate_pause_wallet(self, data: PauseWallet) -> None:
        if self._state.wallet_state in _TERMINAL_STATES:
            raise ApplicationError(
                f"Cannot pause wallet in terminal state: {self._state.wallet_state}",
                type="INVALID_STATE",
                non_retryable=True,
            )

    @workflow.update
    async def resume_wallet(self, data: ResumeWallet) -> ResumeResult:
        self._paused = False
        self._state.manual_review.record_decision(
            decision="approved",
            reviewer_id=data.reviewer_id,
            notes=data.notes,
            decided_at=workflow.now(),
        )
        return ResumeResult(accepted=True)

    @resume_wallet.validator
    def _validate_resume_wallet(self, data: ResumeWallet) -> None:
        if not self._paused:
            raise ApplicationError(
                "Cannot resume a wallet that is not paused.",
                type="INVALID_STATE",
                non_retryable=True,
            )

    # ── Query ─────────────────────────────────────────────────────────────────

    @workflow.query
    def get_status(self) -> WalletStatusQuery:
        return WalletStatusQuery(
            wallet_state=self._state.wallet_state,
            wallet_did=self._state.wallet_did,
            credential_count=len(self._state.credential_ids),
            is_bound=self._state.is_bound_to_connector,
        )
