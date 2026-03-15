"""RevokeCredentialsWorkflow — durable Temporal one-shot workflow.

Orchestrates credential revocation:
  status_updated → bindings_propagated → dependent_procedures_notified
  → (issuer confirmation) → evidence_complete

Replay safety rules:
  - No datetime.now(), uuid4(), or random() calls in workflow code.
  - All I/O is delegated to activity functions.
  - Signals mutate local state only; Queries read local state only.
"""
from __future__ import annotations

from datetime import timedelta

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

from .input import RevocationStartInput, RevocationResult, RevocationStatusQuery
from .state import RevocationWorkflowState
from .messages import ExternalRevocationConfirmed
from .activities import (
    update_credential_status,
    UpdateStatusInput,
    propagate_to_connector_bindings,
    PropagateBindingsInput,
    find_dependent_procedures,
    FindDependentsInput,
    notify_dependent_procedures,
    NotifyDependentsInput,
    freeze_dependent_procedures,
    FreezeDependentsInput,
    record_revocation_evidence,
    RevocationEvidenceInput,
)


@workflow.defn
class RevokeCredentialsWorkflow:
    """One-shot workflow: one instance per revocation request.

    Drives a credential through revocation, binding propagation,
    dependent procedure notification, issuer confirmation, and evidence emission.
    Revocation always completes even if issuer confirmation is not received in time.
    """

    def __init__(self) -> None:
        self._state = RevocationWorkflowState()

    # ------------------------------------------------------------------
    # Main run method
    # ------------------------------------------------------------------

    @workflow.run
    async def run(self, inp: RevocationStartInput) -> RevocationResult:
        # Publish search attributes so the workflow is discoverable.
        workflow.upsert_search_attributes(build_search_attribute_updates({
            TENANT_ID: inp.tenant_id,
            LEGAL_ENTITY_ID: inp.legal_entity_id,
            PROCEDURE_TYPE: "revoke-credentials",
            STATUS: "revoking",
        }))

        # Step 1: Update credential status in the trust domain registry
        await self._update_status(inp)

        # Step 2: Propagate the revocation to connector/wallet bindings
        await self._propagate_bindings(inp)

        # Step 3: Find and handle dependent procedures
        await self._handle_dependents(inp)

        # Step 4: Wait up to 1 hour for issuer async confirmation
        try:
            await workflow.wait_condition(
                lambda: self._state.issuer_confirmed,
                timeout=timedelta(hours=1),
            )
        except Exception:
            # Timeout or unexpected error: log and continue — revocation must always complete.
            # The issuer can still confirm asynchronously via a follow-up signal.
            workflow.logger.warning(
                "Issuer confirmation not received within 1 hour for credential %s — "
                "proceeding with revocation evidence without issuer confirmation.",
                inp.credential_id,
            )

        # Step 5: Record the full revocation evidence chain
        await self._record_evidence(inp)

        workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "completed"}))
        await workflow.wait_condition(workflow.all_handlers_finished)

        return RevocationResult(
            workflow_id=workflow.info().workflow_id,
            status="completed",
            revocation_ref=self._state.revocation_ref,
            notified_procedures=list(self._state.notified_procedure_ids),
            evidence_ref=self._state.evidence_ref,
        )

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    @workflow.signal
    async def external_revocation_confirmed(self, evt: ExternalRevocationConfirmed) -> None:
        """Async callback from the issuer confirming the revocation was recorded."""
        self._state.issuer_confirmed = True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @workflow.query
    def get_status(self) -> RevocationStatusQuery:
        return RevocationStatusQuery(
            revocation_state=self._state.revocation_state,
            revocation_ref=self._state.revocation_ref,
            notified_count=len(self._state.notified_procedure_ids),
            is_complete=self._state.revocation_state == "evidence_complete",
        )

    # ------------------------------------------------------------------
    # Internal phase helpers
    # ------------------------------------------------------------------

    async def _update_status(self, inp: RevocationStartInput) -> None:
        self._state.revocation_state = "status_updating"
        result = await workflow.execute_activity(
            update_credential_status,
            UpdateStatusInput(
                tenant_id=inp.tenant_id,
                credential_id=inp.credential_id,
                credential_type=inp.credential_type,
                revocation_reason=inp.revocation_reason,
                revoked_by=inp.revoked_by,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.revocation_ref = result.revocation_ref
        self._state.revocation_state = "status_updated"

    async def _propagate_bindings(self, inp: RevocationStartInput) -> None:
        self._state.revocation_state = "propagating_bindings"
        result = await workflow.execute_activity(
            propagate_to_connector_bindings,
            PropagateBindingsInput(
                tenant_id=inp.tenant_id,
                credential_id=inp.credential_id,
                credential_type=inp.credential_type,
                revocation_ref=self._state.revocation_ref,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.binding_update_refs = result.binding_refs
        self._state.revocation_state = "bindings_propagated"

    async def _handle_dependents(self, inp: RevocationStartInput) -> None:
        self._state.revocation_state = "finding_dependents"
        find_result = await workflow.execute_activity(
            find_dependent_procedures,
            FindDependentsInput(
                tenant_id=inp.tenant_id,
                credential_id=inp.credential_id,
                credential_type=inp.credential_type,
            ),
            **RPC_OPTIONS,
        )

        dependent_ids = find_result.workflow_ids
        if not dependent_ids:
            self._state.revocation_state = "dependent_procedures_notified"
            return

        # Notify all dependent procedures of the revocation
        notify_result = await workflow.execute_activity(
            notify_dependent_procedures,
            NotifyDependentsInput(
                tenant_id=inp.tenant_id,
                credential_id=inp.credential_id,
                dependent_workflow_ids=dependent_ids,
                revocation_ref=self._state.revocation_ref,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.notified_procedure_ids = notify_result.notified_ids

        # Freeze dependent procedures if the request is urgent
        if inp.urgent and dependent_ids:
            await workflow.execute_activity(
                freeze_dependent_procedures,
                FreezeDependentsInput(
                    tenant_id=inp.tenant_id,
                    credential_id=inp.credential_id,
                    dependent_workflow_ids=dependent_ids,
                ),
                **EXTERNAL_CALL_OPTIONS,
            )

        self._state.revocation_state = "dependent_procedures_notified"

    async def _record_evidence(self, inp: RevocationStartInput) -> None:
        self._state.revocation_state = "recording_evidence"
        result = await workflow.execute_activity(
            record_revocation_evidence,
            RevocationEvidenceInput(
                tenant_id=inp.tenant_id,
                credential_id=inp.credential_id,
                credential_type=inp.credential_type,
                revocation_reason=inp.revocation_reason,
                revoked_by=inp.revoked_by,
                revocation_ref=self._state.revocation_ref,
                notified_procedure_ids=list(self._state.notified_procedure_ids),
                workflow_id=workflow.info().workflow_id,
            ),
            **RPC_OPTIONS,
        )
        self._state.evidence_ref = result.evidence_ref
        self._state.revocation_state = "evidence_complete"
