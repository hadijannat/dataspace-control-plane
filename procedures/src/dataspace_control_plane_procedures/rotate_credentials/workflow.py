"""RotateCredentialsWorkflow — durable, long-lived credential rotation loop.

Lifecycle
---------
1. On first run (RotationStartInput): sets search attributes and enters the
   main loop.
2. On Continue-As-New (RotationCarryState): restores counters and dedupe state
   from the carry snapshot, then re-enters the main loop.
3. Each loop iteration: waits for the scheduled interval (or a ForceRotate
   signal), runs one _rotation_cycle(), then sleeps again.
4. PauseRotation / ResumeRotation updates gate the loop without terminating it.
5. When history depth (approximated by iteration count) reaches the threshold,
   the workflow serialises state and calls continue_as_new.

Signals
-------
- force_rotate  (ForceRotate)  — trigger an immediate cycle

Updates (with validators)
-------------------------
- pause_rotation  (PauseRotation  → PauseResult)
- resume_rotation (ResumeRotation → ResumeResult)

Queries
-------
- get_status → RotationStatusQuery
"""
from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.exceptions import ApplicationError

from dataspace_control_plane_procedures._shared.activity_options import (
    EXTERNAL_CALL_OPTIONS,
    PROVISIONING_OPTIONS,
    RPC_OPTIONS,
)
from dataspace_control_plane_procedures._shared.continue_as_new import (
    CarryEnvelope,
    DedupeState,
    decode_start_input,
    should_continue_as_new,
)
from dataspace_control_plane_procedures._shared.search_attributes import (
    LEGAL_ENTITY_ID,
    PROCEDURE_TYPE,
    STATUS,
    TENANT_ID,
    build_search_attribute_updates,
)

from .activities import (
    BindingUpdateInput,
    EnumerateInput,
    ReissueInput,
    RetireInput,
    ScheduleInput,
    VerifyInput,
    enumerate_expiring_credentials,
    request_credential_reissuance,
    retire_old_credentials,
    schedule_next_rotation,
    update_connector_wallet_bindings,
    verify_new_credential_presentation,
)
from .compensation import run_rotation_compensation
from .errors import PresentationVerifyError
from .input import (
    RotationCarryState,
    RotationResult,
    RotationStartInput,
    RotationStatusQuery,
)
from .messages import ForceRotate, PauseResult, PauseRotation, ResumeResult, ResumeRotation
from .state import RotationWorkflowState

# Trigger Continue-As-New after this many rotation iterations to keep history
# size bounded.  Each iteration emits O(10-20) history events so 80 iterations
# stays comfortably below the 9,000-event threshold used elsewhere in _shared.
_CAN_ITERATION_THRESHOLD = 80


@workflow.defn
class RotateCredentialsWorkflow:
    """Long-lived credential rotation loop for a single (tenant, legal entity, profile) tuple."""

    def __init__(self) -> None:
        self._state = RotationWorkflowState()
        # These are set from the input on first run and carried across CAN boundaries.
        self._tenant_id: str = ""
        self._legal_entity_id: str = ""
        self._credential_profile: str = ""
        self._rotation_interval_days: int = 90
        self._look_ahead_days: int = 30

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    @workflow.run
    async def run(
        self,
        inp: Any,
    ) -> RotationResult:
        """Main workflow loop with explicit Continue-As-New resume support."""
        start_input, carry = decode_start_input(
            inp,
            start_input_type=RotationStartInput,
            state_type=RotationCarryState,
        )
        self._init_from_input(start_input)
        if carry is not None:
            self._restore_carry_state(carry)

        workflow.upsert_search_attributes(build_search_attribute_updates({
            TENANT_ID: self._tenant_id,
            LEGAL_ENTITY_ID: self._legal_entity_id,
            PROCEDURE_TYPE: "rotate-credentials",
            STATUS: "running",
        }))

        await self._main_loop(start_input)

        # In practice this workflow never returns (it either loops forever or
        # continues-as-new).  This return satisfies the type checker.
        return RotationResult(
            workflow_id=workflow.info().workflow_id,
            status=self._state.rotation_state,
            rotated_count=self._state.rotated_count,
            next_rotation_at=self._state.last_rotation_at,
        )

    # ------------------------------------------------------------------
    # Internal initialisation helpers
    # ------------------------------------------------------------------

    def _init_from_input(self, inp: RotationStartInput) -> None:
        self._tenant_id = inp.tenant_id
        self._legal_entity_id = inp.legal_entity_id
        self._credential_profile = inp.credential_profile
        self._rotation_interval_days = inp.rotation_interval_days
        self._look_ahead_days = inp.look_ahead_days

    def _restore_carry_state(self, carry: RotationCarryState) -> None:
        self._state.rotation_state = carry.rotation_state
        self._state.last_rotation_at = carry.last_rotation_at
        self._state.rotated_count = carry.rotated_count_total
        self._state.is_paused = carry.is_paused
        self._state.dedupe = DedupeState.from_snapshot(carry.dedupe_ids)
        self._state.iteration = carry.iteration

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def _main_loop(self, start_input: RotationStartInput) -> None:
        """Runs rotation cycles indefinitely, sleeping between each one."""
        while True:
            # Honour pause before doing any work.
            if self._state.is_paused:
                await workflow.wait_condition(lambda: not self._state.is_paused)

            # Run one full rotation cycle.
            await self._rotation_cycle()

            # Clear force flag; the cycle has consumed it.
            self._state.force_rotate_requested = False
            self._state.iteration += 1

            # Continue-As-New boundary: keep history bounded.
            if should_continue_as_new(self._state.iteration, threshold=_CAN_ITERATION_THRESHOLD):
                await workflow.wait_condition(workflow.all_handlers_finished)
                workflow.continue_as_new(
                    CarryEnvelope(
                        start_input=start_input,
                        state=RotationCarryState(
                            rotation_state=self._state.rotation_state,
                            last_rotation_at=self._state.last_rotation_at,
                            rotated_count_total=self._state.rotated_count,
                            is_paused=self._state.is_paused,
                            dedupe_ids=self._state.dedupe.snapshot(),
                            iteration=self._state.iteration,
                        ),
                    )
                )

            # Sleep until the next scheduled rotation or until a signal fires.
            try:
                await workflow.wait_condition(
                    lambda: self._state.force_rotate_requested or self._state.is_paused,
                    timeout=timedelta(days=self._rotation_interval_days),
                )
            except asyncio.TimeoutError:
                # Normal expiry — time for the next scheduled cycle.
                pass

    # ------------------------------------------------------------------
    # Core rotation cycle
    # ------------------------------------------------------------------

    async def _rotation_cycle(self) -> None:
        """Execute one complete credential rotation cycle.

        Phases (matches RotationWorkflowState.rotation_state values):
          scan_started → replacement_requested → replacement_verified
          → bindings_updated → old_credentials_retired
        """
        tenant_id = self._tenant_id
        legal_entity_id = self._legal_entity_id
        credential_profile = self._credential_profile

        # ---- Phase 1: scan for expiring credentials ----
        self._state.rotation_state = "scan_started"
        enum_result = await workflow.execute_activity(
            enumerate_expiring_credentials,
            EnumerateInput(
                tenant_id=tenant_id,
                legal_entity_id=legal_entity_id,
                credential_profile=credential_profile,
                look_ahead_days=self._look_ahead_days,
            ),
            **RPC_OPTIONS,
        )
        self._state.expiring_credential_ids = list(enum_result.credential_ids)

        if not self._state.expiring_credential_ids:
            # No-op cycle: nothing to rotate.
            return

        # ---- Phase 2: request reissuance ----
        self._state.rotation_state = "replacement_requested"
        self._state.compensation.record(
            action="credential_reissuance",
            resource_id=f"{tenant_id}:{legal_entity_id}",
        )
        reissue_result = await workflow.execute_activity(
            request_credential_reissuance,
            ReissueInput(
                tenant_id=tenant_id,
                legal_entity_id=legal_entity_id,
                credential_profile=credential_profile,
                expiring_credential_ids=list(self._state.expiring_credential_ids),
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.new_credential_ids = list(reissue_result.new_credential_ids)

        # ---- Phase 3: verify new credentials ----
        self._state.rotation_state = "replacement_verified"
        verify_result = await workflow.execute_activity(
            verify_new_credential_presentation,
            VerifyInput(
                tenant_id=tenant_id,
                legal_entity_id=legal_entity_id,
                new_credential_ids=list(self._state.new_credential_ids),
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        if not verify_result.ok:
            await run_rotation_compensation(self._state, tenant_id, legal_entity_id)
            raise PresentationVerifyError(
                "New credential presentation verification failed; "
                f"failed IDs: {verify_result.failed_ids}",
                non_retryable=True,
            )

        # ---- Phase 4: update connector / wallet bindings ----
        self._state.rotation_state = "bindings_updated"
        await workflow.execute_activity(
            update_connector_wallet_bindings,
            BindingUpdateInput(
                tenant_id=tenant_id,
                legal_entity_id=legal_entity_id,
                old_credential_ids=list(self._state.expiring_credential_ids),
                new_credential_ids=list(self._state.new_credential_ids),
            ),
            **PROVISIONING_OPTIONS,
        )

        # ---- Phase 5: retire old credentials ----
        self._state.rotation_state = "old_credentials_retired"
        await workflow.execute_activity(
            retire_old_credentials,
            RetireInput(
                tenant_id=tenant_id,
                legal_entity_id=legal_entity_id,
                old_credential_ids=list(self._state.expiring_credential_ids),
            ),
            **EXTERNAL_CALL_OPTIONS,
        )

        # ---- Phase 6: update counters and schedule next rotation ----
        self._state.rotated_count += len(self._state.expiring_credential_ids)
        schedule_result = await workflow.execute_activity(
            schedule_next_rotation,
            ScheduleInput(
                tenant_id=tenant_id,
                legal_entity_id=legal_entity_id,
                credential_profile=credential_profile,
                rotation_interval_days=self._rotation_interval_days,
                last_rotation_at=self._state.last_rotation_at,
            ),
            **RPC_OPTIONS,
        )
        self._state.last_rotation_at = schedule_result.next_rotation_at

        # Clean up per-cycle transient state.
        self._state.expiring_credential_ids = []
        self._state.new_credential_ids = []

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    @workflow.signal
    async def force_rotate(self, sig: ForceRotate) -> None:
        """Trigger an immediate rotation cycle, bypassing the scheduled timer.

        Duplicate signals with the same event_id are silently discarded by
        DedupeState to prevent double-rotation under at-least-once delivery.
        """
        if self._state.dedupe.is_duplicate(sig.event_id):
            return
        self._state.dedupe.mark_handled(sig.event_id)
        self._state.force_rotate_requested = True

    # ------------------------------------------------------------------
    # Updates (with validators)
    # ------------------------------------------------------------------

    @workflow.update
    async def pause_rotation(self, cmd: PauseRotation) -> PauseResult:
        """Pause future rotation cycles.  In-progress cycles complete first."""
        self._state.is_paused = True
        workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "paused"}))
        return PauseResult(accepted=True)

    @pause_rotation.validator
    def validate_pause_rotation(self, cmd: PauseRotation) -> None:
        if self._state.is_paused:
            raise ApplicationError("Rotation is already paused", non_retryable=True)

    @workflow.update
    async def resume_rotation(self, cmd: ResumeRotation) -> ResumeResult:
        """Resume a previously paused rotation loop."""
        self._state.is_paused = False
        workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "running"}))
        return ResumeResult(accepted=True)

    @resume_rotation.validator
    def validate_resume_rotation(self, cmd: ResumeRotation) -> None:
        if not self._state.is_paused:
            raise ApplicationError("Rotation is not paused", non_retryable=True)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @workflow.query
    def get_status(self) -> RotationStatusQuery:
        """Return a point-in-time snapshot of workflow state for observability."""
        return RotationStatusQuery(
            rotation_state=self._state.rotation_state,
            expiring_count=len(self._state.expiring_credential_ids),
            rotated_count=self._state.rotated_count,
            next_rotation_at=self._state.last_rotation_at,
            is_paused=self._state.is_paused,
        )
