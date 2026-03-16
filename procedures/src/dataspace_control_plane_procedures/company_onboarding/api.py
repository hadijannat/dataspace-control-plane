"""Public exports for company_onboarding procedure."""
from dataspace_control_plane_procedures.registry import build_definition

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
    bind_hierarchy,
    run_compliance_baseline,
    emit_onboarding_evidence,
    compensate_registration,
    compensate_wallet_bootstrap,
    compensate_connector_bootstrap,
)

ALL_WORKFLOWS = [CompanyOnboardingWorkflow]
ALL_ACTIVITIES = [
    preflight_validate,
    register_legal_entity,
    request_approval,
    bootstrap_wallet,
    bootstrap_connector,
    bind_hierarchy,
    run_compliance_baseline,
    emit_onboarding_evidence,
    compensate_registration,
    compensate_wallet_bootstrap,
    compensate_connector_bootstrap,
]

WorkflowClass = CompanyOnboardingWorkflow
StartInput = OnboardingStartInput
Result = OnboardingResult
StatusQuery = OnboardingStatusQuery
manifest = MANIFEST
definition = build_definition(
    api_module_name=__name__,
    manifest=MANIFEST,
    start_input_type=OnboardingStartInput,
    status_query_type=OnboardingStatusQuery,
    workflow_types=ALL_WORKFLOWS,
    activity_functions=ALL_ACTIVITIES,
)


def register() -> None:
    """Backward-compatible hook for legacy callers."""
    from dataspace_control_plane_procedures.registry import _register_definition

    _register_definition(definition)


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
    "WorkflowClass",
    "StartInput",
    "Result",
    "StatusQuery",
    "manifest",
    "definition",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "register",
]
