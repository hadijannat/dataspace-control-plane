"""Compensation orchestration for the company_onboarding procedure.

Runs compensation activities in reverse order of recorded actions.
Must be called only from inside a workflow function context.
"""
from __future__ import annotations

from temporalio import workflow

from .state import OnboardingWorkflowState
from .activities import compensate_registration, CompensateRegistrationInput


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
            state.compensation.mark_compensated(marker.action, marker.resource_id)
