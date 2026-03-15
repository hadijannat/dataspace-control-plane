"""ConnectorBootstrapWorkflow — durable Temporal entity workflow.

Provisions a dataspace connector through its full lifecycle:
  desired → plan_ready → infra_applied → runtime_healthy →
  wallet_linked → dataspace_registered → discovery_verified.

The workflow ID is stable per connector binding so duplicate starts
are safely deduplicated by Temporal's conflict policy.

Replay safety rules:
  - No datetime.now(), uuid4(), or random() calls in workflow code.
  - All I/O is delegated to activity functions.
  - Signals, Updates, and Queries only mutate/read local state.
"""
from __future__ import annotations

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
    LONG_POLL_OPTIONS,
)
from dataspace_control_plane_procedures._shared.continue_as_new import (
    CarryEnvelope,
    decode_start_input,
    should_continue_as_new,
)

from .input import (
    ConnectorStartInput,
    ConnectorResult,
    ConnectorCarryState,
    ConnectorStatusQuery,
)
from .state import ConnectorWorkflowState
from .messages import (
    HealthDegraded,
    WalletBound,
    ForceHealthCheckInput,
    ForceHealthCheckResult,
)
from .activities import (
    plan_connector_infra,
    apply_connector_infra,
    wait_for_runtime_healthy,
    link_wallet_to_connector,
    register_in_dataspace,
    verify_discovery,
    ConnectorPlanInput,
    ConnectorApplyInput,
    ConnectorHealthInput,
    WalletLinkInput,
    DataspaceRegInput,
    DiscoveryVerifyInput,
)
from .compensation import run_connector_compensation
from .errors import (
    ConnectorBootstrapError,
    InfraApplyError,
    HealthCheckError,
    DataspaceRegistrationError,
    WalletLinkError,
)


@workflow.defn
class ConnectorBootstrapWorkflow:
    """Entity workflow: one instance per connector binding, stable workflow ID.

    Drives a connector through full provisioning and registers it in the
    dataspace discovery catalog.
    """

    def __init__(self) -> None:
        self._state = ConnectorWorkflowState()
        self._wallet_ref: str = ""

    # ------------------------------------------------------------------
    # Main run method
    # ------------------------------------------------------------------

    @workflow.run
    async def run(
        self,
        inp: Any,
    ) -> ConnectorResult:
        start_input, carry = decode_start_input(
            inp,
            start_input_type=ConnectorStartInput,
            state_type=ConnectorCarryState,
        )
        if carry is not None:
            self._restore_from_carry(carry)

        workflow.upsert_search_attributes(build_search_attribute_updates({
            TENANT_ID: start_input.tenant_id,
            LEGAL_ENTITY_ID: start_input.legal_entity_id,
            PROCEDURE_TYPE: "connector-bootstrap",
            STATUS: "running",
        }))

        try:
            await self._plan(start_input)
            await self._checkpoint(start_input)

            await self._apply(start_input)
            await self._checkpoint(start_input)

            await self._await_healthy(start_input)
            await self._checkpoint(start_input)

            await self._link_wallet(start_input)
            await self._checkpoint(start_input)

            await self._register_dataspace(start_input)
            await self._checkpoint(start_input)

            await self._verify_discovery(start_input)

        except CancelledError:
            await run_connector_compensation(self._state)
            raise
        except Exception:
            await run_connector_compensation(self._state)
            raise

        workflow.upsert_search_attributes(build_search_attribute_updates({STATUS: "completed"}))
        self._state.connector_state = "discovery_verified"

        await workflow.wait_condition(workflow.all_handlers_finished)

        return ConnectorResult(
            workflow_id=workflow.info().workflow_id,
            status="completed",
            connector_binding_id=self._state.connector_binding_id,
            dataspace_connector_id=self._state.dataspace_connector_id,
            discovery_endpoint=self._state.discovery_endpoint,
        )

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    @workflow.signal
    async def health_degraded(self, evt: HealthDegraded) -> None:
        """Runtime health monitor reports connector degradation."""
        if self._state.dedupe.is_duplicate(evt.event_id):
            return
        self._state.dedupe.mark_handled(evt.event_id)

        self._state.connector_state = "degraded"
        self._state.error_reason = evt.reason
        self._state.manual_review.request(
            f"Connector degraded: {evt.reason}",
            review_id=evt.event_id,
            requested_at=workflow.now(),
        )

    @workflow.signal
    async def wallet_bound(self, evt: WalletBound) -> None:
        """External signal that wallet credentials have been bound."""
        if self._state.dedupe.is_duplicate(evt.event_id):
            return
        self._state.dedupe.mark_handled(evt.event_id)

        self._state.wallet_linked = True
        self._wallet_ref = evt.wallet_ref
        self._state.wallet_ref = evt.wallet_ref

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------

    @workflow.update
    async def force_health_check(self, cmd: ForceHealthCheckInput) -> ForceHealthCheckResult:
        """Trigger an immediate health check and return the result."""
        result = await workflow.execute_activity(
            wait_for_runtime_healthy,
            ConnectorHealthInput(
                connector_url=self._state.connector_binding_id,  # use binding as proxy
                connector_binding_id=self._state.connector_binding_id,
                max_polls=1,
            ),
            **RPC_OPTIONS,
        )
        self._state.last_health_check = "healthy" if result.is_healthy else "unhealthy"
        if not result.is_healthy:
            self._state.connector_state = "degraded"

        return ForceHealthCheckResult(
            health_status=result.health_status,
            is_healthy=result.is_healthy,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @workflow.query
    def get_status(self) -> ConnectorStatusQuery:
        return ConnectorStatusQuery(
            state=self._state.connector_state,
            blocking_reason=self._state.manual_review.blocking_reason,
            connector_url=self._state.connector_binding_id,
            dataspace_registered=self._state.dataspace_registered,
            wallet_linked=self._state.wallet_linked,
            is_healthy=self._state.connector_state not in ("degraded", "desired"),
        )

    # ------------------------------------------------------------------
    # Internal phase helpers
    # ------------------------------------------------------------------

    def _restore_from_carry(self, carry: ConnectorCarryState) -> None:
        """Restore workflow state from a Continue-As-New carry payload."""
        self._state.connector_state = carry.connector_state
        self._state.connector_binding_id = carry.connector_binding_id
        self._state.dataspace_connector_id = carry.dataspace_connector_id
        self._state.discovery_endpoint = carry.discovery_endpoint
        self._state.wallet_ref = carry.wallet_ref
        self._state.plan_ref = carry.plan_ref
        self._state.infra_apply_ref = carry.infra_apply_ref
        self._state.wallet_linked = carry.wallet_linked
        self._state.dataspace_registered = carry.dataspace_registered
        self._state.last_health_check = carry.last_health_check
        self._state.manual_review = self._state.manual_review.from_snapshot(carry.manual_review)
        self._state.compensation = self._state.compensation.from_snapshot(carry.compensation_markers)
        self._state.iteration = carry.iteration
        self._state.dedupe = self._state.dedupe.from_snapshot(carry.dedupe_ids)
        self._wallet_ref = carry.wallet_ref

    async def _checkpoint(self, inp: ConnectorStartInput) -> None:
        """Continue-As-New if history is approaching the threshold."""
        info = workflow.info()
        if should_continue_as_new(info.get_current_history_length()):
            await workflow.wait_condition(workflow.all_handlers_finished)
            carry = ConnectorCarryState(
                connector_state=self._state.connector_state,
                connector_binding_id=self._state.connector_binding_id,
                dataspace_connector_id=self._state.dataspace_connector_id,
                discovery_endpoint=self._state.discovery_endpoint,
                plan_ref=self._state.plan_ref,
                infra_apply_ref=self._state.infra_apply_ref,
                wallet_ref=self._state.wallet_ref,
                wallet_linked=self._state.wallet_linked,
                dataspace_registered=self._state.dataspace_registered,
                last_health_check=self._state.last_health_check,
                dedupe_ids=self._state.dedupe.snapshot(),
                manual_review=self._state.manual_review.snapshot(),
                compensation_markers=self._state.compensation.snapshot(),
                iteration=self._state.iteration + 1,
            )
            workflow.continue_as_new(CarryEnvelope(start_input=inp, state=carry))

    async def _plan(self, inp: ConnectorStartInput) -> None:
        """Phase: generate an infra plan via the provisioning agent."""
        if self._state.connector_state not in ("desired",):
            return  # Already planned; skip on Continue-As-New restart.

        result = await workflow.execute_activity(
            plan_connector_infra,
            ConnectorPlanInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                environment=inp.environment,
                binding_name=inp.binding_name,
                connector_url=inp.connector_url,
                pack_id=inp.pack_id,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.plan_ref = result.plan_ref
        self._state.connector_binding_id = result.connector_binding_id
        self._state.connector_state = "plan_ready"

    async def _apply(self, inp: ConnectorStartInput) -> None:
        """Phase: apply the infra plan to provision the connector."""
        if self._state.connector_state not in ("plan_ready",):
            return  # Already applied; skip on Continue-As-New restart.

        result = await workflow.execute_activity(
            apply_connector_infra,
            ConnectorApplyInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                plan_ref=self._state.plan_ref,
                connector_binding_id=self._state.connector_binding_id,
            ),
            **PROVISIONING_OPTIONS,
        )
        self._state.infra_apply_ref = result.infra_apply_ref
        self._state.compensation.record("apply_connector_infra", result.infra_apply_ref)
        self._state.connector_state = "infra_applied"

    async def _await_healthy(self, inp: ConnectorStartInput) -> None:
        """Phase: poll connector health until runtime is ready."""
        if self._state.connector_state not in ("infra_applied",):
            return  # Already healthy; skip on Continue-As-New restart.

        result = await workflow.execute_activity(
            wait_for_runtime_healthy,
            ConnectorHealthInput(
                connector_url=inp.connector_url,
                connector_binding_id=self._state.connector_binding_id,
            ),
            **LONG_POLL_OPTIONS,
        )
        if not result.is_healthy:
            raise HealthCheckError(
                f"Connector {self._state.connector_binding_id} did not become healthy"
            )
        self._state.last_health_check = result.health_status
        self._state.connector_state = "runtime_healthy"

    async def _link_wallet(self, inp: ConnectorStartInput) -> None:
        """Phase: bind wallet credentials to the connector.

        If a WalletBound signal arrived before this phase, use it directly.
        Otherwise call the link activity with the wallet_ref from the input.
        """
        if self._state.connector_state not in ("runtime_healthy",):
            return  # Already linked; skip on Continue-As-New restart.

        wallet_ref = self._wallet_ref or self._state.wallet_ref or inp.wallet_ref
        if wallet_ref:
            result = await workflow.execute_activity(
                link_wallet_to_connector,
                WalletLinkInput(
                    tenant_id=inp.tenant_id,
                    legal_entity_id=inp.legal_entity_id,
                    connector_binding_id=self._state.connector_binding_id,
                    wallet_ref=wallet_ref,
                ),
                **PROVISIONING_OPTIONS,
            )
            if not result.linked:
                raise WalletLinkError(
                    f"Failed to link wallet {wallet_ref} to {self._state.connector_binding_id}"
                )
            self._state.wallet_linked = True
            self._state.wallet_ref = wallet_ref

        self._state.connector_state = "wallet_linked"

    async def _register_dataspace(self, inp: ConnectorStartInput) -> None:
        """Phase: register the connector in the DSP catalog."""
        if self._state.connector_state not in ("wallet_linked",):
            return  # Already registered; skip on Continue-As-New restart.

        result = await workflow.execute_activity(
            register_in_dataspace,
            DataspaceRegInput(
                tenant_id=inp.tenant_id,
                legal_entity_id=inp.legal_entity_id,
                connector_binding_id=self._state.connector_binding_id,
                connector_url=inp.connector_url,
                pack_id=inp.pack_id,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        self._state.dataspace_connector_id = result.dataspace_connector_id
        self._state.dataspace_registered = True
        self._state.compensation.record("register_in_dataspace", result.dataspace_connector_id)
        self._state.connector_state = "dataspace_registered"

    async def _verify_discovery(self, inp: ConnectorStartInput) -> None:
        """Phase: confirm the connector appears in the discovery service."""
        if self._state.connector_state not in ("dataspace_registered",):
            return  # Already verified; skip on Continue-As-New restart.

        result = await workflow.execute_activity(
            verify_discovery,
            DiscoveryVerifyInput(
                dataspace_connector_id=self._state.dataspace_connector_id,
                pack_id=inp.pack_id,
            ),
            **EXTERNAL_CALL_OPTIONS,
        )
        if not result.found:
            raise ConnectorBootstrapError(
                f"Connector {self._state.dataspace_connector_id} not found in discovery"
            )
        self._state.discovery_endpoint = result.discovery_endpoint
