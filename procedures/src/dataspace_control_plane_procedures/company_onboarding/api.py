"""Public exports for company_onboarding procedure."""
from .workflow import CompanyOnboardingWorkflow
from .manifest import MANIFEST, WORKFLOW_TYPE, TASK_QUEUE
from .input import OnboardingStartInput, OnboardingResult, OnboardingStatusQuery, OnboardingCarryState
from .messages import ExternalApprovalEvent, ApproveCaseInput, RejectCaseInput
from .activities import (
    preflight_validate,
    register_legal_entity,
    request_approval,
    bootstrap_wallet,
    bootstrap_connector,
    run_compliance_baseline,
    emit_onboarding_evidence,
    compensate_registration,
)

ALL_WORKFLOWS = [CompanyOnboardingWorkflow]
ALL_ACTIVITIES = [
    preflight_validate,
    register_legal_entity,
    request_approval,
    bootstrap_wallet,
    bootstrap_connector,
    run_compliance_baseline,
    emit_onboarding_evidence,
    compensate_registration,
]


def register() -> None:
    """Called by registry.populate_from_procedures() at worker startup."""
    from dataspace_control_plane_procedures.registry import _register
    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


__all__ = [
    "CompanyOnboardingWorkflow",
    "MANIFEST",
    "WORKFLOW_TYPE",
    "TASK_QUEUE",
    "OnboardingStartInput",
    "OnboardingResult",
    "OnboardingStatusQuery",
    "OnboardingCarryState",
    "ExternalApprovalEvent",
    "ApproveCaseInput",
    "RejectCaseInput",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "register",
]
