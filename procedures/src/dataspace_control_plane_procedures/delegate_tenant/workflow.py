"""DelegateTenantWorkflow — durable Temporal entity workflow.

Orchestrates parent-child legal entity delegation:
  child_topology_created → identifiers_bound → connector_mode_decided →
  trust_scope_ready → delegation_verified.

Branches:
  - shared connector: explicit delegation scope applied on parent connector.
  - dedicated connector: records note for connector_bootstrap child workflow.

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
    build_search_attribute_updates,
)
from dataspace_control_plane_procedures._shared.activity_options import (
    PROVISIONING_OPTIONS,
    EXTERNAL_CALL_OPTIONS,
    RPC_OPTIONS,
)

from .input import DelegationStartInput, DelegationResult
from .state import DelegationWorkflowState
from .messages import (
    ConnectorModeDecided,
    ApproveCrossBorderDelegation,
    ApprovalResult,
    RejectDelegation,
    RejectionResult,
)
from .activities import (
    create_child_topology,
    ChildTopologyInput,
    bind_child_identifiers,
    IdentifierBindInput,
    determine_connector_mode,
    ConnectorModeInput,
    apply_shared_connector_delegation,
    SharedConnectorInput,
    apply_trust_scope,
    TrustScopeInput,
    verify_tenant_isolation,
    IsolationVerifyInput,
    emit_delegation_evidence,
    DelegationEvidenceInput,
)
from .compensation import run_delegation_compensation
from .errors import (
    TopologyCreationError,
    IdentifierBindingError,
    ConnectorModeError,
    TrustScopeError,
    DelegationVerificationError,
)


@workflow.defn
class DelegateTenantWorkflow:
    """Entity workflow: one instance per parent–child delegation pair.

    Drives a child legal entity through the full delegation lifecycle and
    emits a structured audit event on completion.
    """

    def __init__(self) -> None:
        self._state = DelegationWorkflowState()
        self._review_decided: bool = False

    # ------------------------------------------------------------------
    # Main run method
    # ------------------------------------------------------------------

    @workflow.run
    async def run(self, inp: DelegationStartInput) -> DelegationResult:
        workflow.upsert_search_attributes(build_search_attribute_updates({
            TENANT_ID: inp.tenant_id,
            LEGAL_ENTITY_ID: inp.legal_entity_id,
            PROCEDURE_TYPE: "delegate-tenant",
            STATUS: "running",
        }))

        try:
            await self._create_child_topology(inp)
            await self._bind_identifiers(inp)
            await self._determine_connector_mode(inp)

            if self._state.connector_mode == "shared":
                await self._apply_shared_delegation(inp)
            else:
                # Dedicated: note that a connector_bootstrap child workflow
                # must be spawned by the caller / scheduler.
                # The connector_ref remains empty until that workflow completes.
                workflow.logger.info(
                    "delegate_tenant: dedicated connector mode — "
                    "connector_bootstrap child workflow must be spawned separately"
                )

            await self._apply_trust_scope(inp)
            await self._verify_isolation(inp)
            await self._emit_evidence(inp)

        except CancelledError:
            await run_delegation_compensation(self._state)
            raise
        except Exception:
            await run_delegation_compensation(self._state)
            raise

        workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "completed"}))
        self._state.delegation_state = "delegation_verified"
        self._state.is_verified = True

        await workflow.wait_condition(workflow.all_handlers_finished)

        return DelegationResult(
            workflow_id=workflow.info().workflow_id,
            status="completed",
            child_topology_ref=self._state.child_topology_ref,
            delegation_ref=self._state.delegation_ref,
            connector_mode=self._state.connector_mode,
            connector_ref=self._state.connector_ref,
        )

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    @workflow.signal
    async def connector_mode_decided(self, evt: ConnectorModeDecided) -> None:
        """Operator overrides the auto connector-mode selection."""
        if self._state.dedupe.is_duplicate(evt.event_id):
            return
        self._state.dedupe.mark_handled(evt.event_id)

        if evt.mode not in ("shared", "dedicated"):
            return
        self._state.connector_mode = evt.mode
        self._state.connector_ref = evt.connector_ref
        self._state.delegation_state = "connector_mode_decided"

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------

    @workflow.update
    async def approve_cross_border_delegation(
        self, cmd: ApproveCrossBorderDelegation
    ) -> ApprovalResult:
        """Reviewer approves a pending cross-border delegation."""
        self._state.manual_review.record_decision(
            "approved",
            cmd.reviewer_id,
            cmd.notes,
            decided_at=workflow.now(),
        )
        self._review_decided = True
        return ApprovalResult(accepted=True)

    @approve_cross_border_delegation.validator
    def validate_approve_cross_border_delegation(self, cmd: ApproveCrossBorderDelegation) -> None:
        if not self._state.manual_review.is_pending:
            raise ApplicationError("No pending cross-border review to approve")

    @workflow.update
    async def reject_delegation(self, cmd: RejectDelegation) -> RejectionResult:
        """Reviewer rejects the delegation."""
        self._state.manual_review.record_decision(
            "rejected",
            cmd.reviewer_id,
            cmd.reason,
            decided_at=workflow.now(),
        )
        self._state.is_rejected = True
        self._review_decided = True
        return RejectionResult(accepted=True)

    @reject_delegation.validator
    def validate_reject_delegation(self, cmd: RejectDelegation) -> None:
        if not self._state.manual_review.is_pending:
            raise ApplicationError("No pending delegation review to reject")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @workflow.query
    def get_status(self):
        from .input import DelegationStatusQuery
        return DelegationStatusQuery(
            delegation_state=self._state.delegation_state,
            connector_mode=self._state.connector_mode,
            is_verified=self._state.is_verified,
            blocking_reason=self._state.manual_review.blocking_reason,
        )

    # ------------------------------------------------------------------
    # Internal phase helpers
    # ------------------------------------------------------------------

    async def _create_child_topology(self, inp: DelegationStartInput) -> None:
        self._state.delegation_state = "pending"
        result = await workflow.execute_activity(
            create_child_topology,
            ChildTopologyInput(
                tenant_id=inp.tenant_id,
                parent_legal_entity_id=inp.parent_legal_entity_id,
                child_legal_entity_id=inp.legal_entity_id,
                child_legal_entity_name=inp.child_legal_entity_name,
            ),
            **PROVISIONING_OPTIONS,
        )
        if not result.child_topology_ref:
            raise TopologyCreationError("create_child_topology returned an empty ref")
        self._state.child_topology_ref = result.child_topology_ref
        self._state.compensation.record("create_child_topology", result.child_topology_ref)
        self._state.delegation_state = "child_topology_created"

    async def _bind_identifiers(self, inp: DelegationStartInput) -> None:
        result = await workflow.execute_activity(
            bind_child_identifiers,
            IdentifierBindInput(
                tenant_id=inp.tenant_id,
                child_legal_entity_id=inp.legal_entity_id,
                child_bpnl=inp.child_bpnl,
                child_topology_ref=self._state.child_topology_ref,
            ),
            **RPC_OPTIONS,
        )
        if not result.bound:
            raise IdentifierBindingError("bind_child_identifiers failed")
        self._state.delegation_state = "identifiers_bound"

    async def _determine_connector_mode(self, inp: DelegationStartInput) -> None:
        result = await workflow.execute_activity(
            determine_connector_mode,
            ConnectorModeInput(
                tenant_id=inp.tenant_id,
                parent_legal_entity_id=inp.parent_legal_entity_id,
                child_legal_entity_id=inp.legal_entity_id,
                requested_mode=inp.connector_mode,
                parent_connector_ref=inp.parent_connector_ref,
                pack_id=inp.pack_id,
            ),
            **RPC_OPTIONS,
        )

        if result.mode not in ("shared", "dedicated"):
            raise ConnectorModeError(f"Unsupported connector mode returned: {result.mode!r}")

        self._state.connector_mode = result.mode
        self._state.connector_ref = result.connector_ref

        if result.requires_review:
            self._state.manual_review.request(
                "cross-border delegation requires manual review",
                review_id=f"xborder:{inp.tenant_id}:{inp.legal_entity_id}",
                requested_at=workflow.now(),
            )
            await workflow.wait_condition(lambda: self._review_decided)

            if self._state.is_rejected or self._state.manual_review.is_rejected:
                raise ApplicationError("Cross-border delegation rejected by reviewer")

        self._state.delegation_state = "connector_mode_decided"

    async def _apply_shared_delegation(self, inp: DelegationStartInput) -> None:
        result = await workflow.execute_activity(
            apply_shared_connector_delegation,
            SharedConnectorInput(
                tenant_id=inp.tenant_id,
                parent_legal_entity_id=inp.parent_legal_entity_id,
                child_legal_entity_id=inp.legal_entity_id,
                parent_connector_ref=inp.parent_connector_ref,
                child_topology_ref=self._state.child_topology_ref,
            ),
            **PROVISIONING_OPTIONS,
        )
        if not result.delegation_ref:
            raise ConnectorModeError("apply_shared_connector_delegation returned empty delegation_ref")
        self._state.delegation_ref = result.delegation_ref
        self._state.compensation.record(
            "apply_shared_connector_delegation", result.delegation_ref
        )

    async def _apply_trust_scope(self, inp: DelegationStartInput) -> None:
        result = await workflow.execute_activity(
            apply_trust_scope,
            TrustScopeInput(
                tenant_id=inp.tenant_id,
                child_legal_entity_id=inp.legal_entity_id,
                delegation_ref=self._state.delegation_ref,
                connector_mode=self._state.connector_mode,
            ),
            **RPC_OPTIONS,
        )
        if not result.scope_refs:
            raise TrustScopeError("apply_trust_scope returned no scope_refs")
        self._state.trust_scope_refs = list(result.scope_refs)
        self._state.delegation_state = "trust_scope_ready"

    async def _verify_isolation(self, inp: DelegationStartInput) -> None:
        result = await workflow.execute_activity(
            verify_tenant_isolation,
            IsolationVerifyInput(
                tenant_id=inp.tenant_id,
                parent_legal_entity_id=inp.parent_legal_entity_id,
                child_legal_entity_id=inp.legal_entity_id,
                child_topology_ref=self._state.child_topology_ref,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        if not result.ok:
            raise DelegationVerificationError(
                f"Tenant isolation verification failed: {result.reason}"
            )

    async def _emit_evidence(self, inp: DelegationStartInput) -> None:
        await workflow.execute_activity(
            emit_delegation_evidence,
            DelegationEvidenceInput(
                tenant_id=inp.tenant_id,
                parent_legal_entity_id=inp.parent_legal_entity_id,
                child_legal_entity_id=inp.legal_entity_id,
                delegation_ref=self._state.delegation_ref,
                connector_mode=self._state.connector_mode,
                workflow_id=workflow.info().workflow_id,
            ),
            **RPC_OPTIONS,
        )
