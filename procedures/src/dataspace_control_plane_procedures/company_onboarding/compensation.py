"""Compensation orchestration for the company_onboarding procedure.

Runs compensation activities in reverse order of recorded actions.
Must be called only from inside a workflow function context.
"""
from __future__ import annotations

from temporalio import workflow

from .state import OnboardingWorkflowState
from .activities import (
    CompensateConnectorBootstrapInput,
    CompensateRegistrationInput,
    CompensateWalletBootstrapInput,
    compensate_connector_bootstrap,
    compensate_registration,
    compensate_wallet_bootstrap,
)


async def run_compensation(state: OnboardingWorkflowState) -> None:
    """Execute compensation in reverse order of recorded actions."""
    from dataspace_control_plane_procedures._shared.activity_options import PROVISIONING_OPTIONS

    for marker in state.compensation.pending():
        if marker.action == "register_legal_entity":
            await workflow.execute_activity(
                compensate_registration,
                CompensateRegistrationInput(registration_ref=marker.resource_id),
                **PROVISIONING_OPTIONS,
            )
            state.compensation.mark_compensated(
                marker.action,
                marker.resource_id,
                completed_at=workflow.now(),
            )
        elif marker.action == "bootstrap_wallet":
            await workflow.execute_activity(
                compensate_wallet_bootstrap,
                CompensateWalletBootstrapInput(wallet_ref=marker.resource_id),
                **PROVISIONING_OPTIONS,
            )
            state.compensation.mark_compensated(
                marker.action,
                marker.resource_id,
                completed_at=workflow.now(),
            )
        elif marker.action == "bootstrap_connector":
            await workflow.execute_activity(
                compensate_connector_bootstrap,
                CompensateConnectorBootstrapInput(connector_binding_id=marker.resource_id),
                **PROVISIONING_OPTIONS,
            )
            state.compensation.mark_compensated(
                marker.action,
                marker.resource_id,
                completed_at=workflow.now(),
            )
