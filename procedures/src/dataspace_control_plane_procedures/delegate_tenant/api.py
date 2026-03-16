"""Public exports for delegate_tenant procedure."""
from dataspace_control_plane_procedures.registry import build_definition

from .workflow import DelegateTenantWorkflow
from .manifest import MANIFEST, WORKFLOW_TYPE, TASK_QUEUE
from .input import (
    DelegationStartInput,
    DelegationResult,
    DelegationStatusQuery,
    DelegationCarryState,
)
from .messages import (
    ConnectorModeDecided,
    ApproveCrossBorderDelegation,
    ApprovalResult,
    RejectDelegation,
    RejectionResult,
)
from .activities import (
    create_child_topology,
    bind_child_identifiers,
    determine_connector_mode,
    apply_shared_connector_delegation,
    apply_trust_scope,
    verify_tenant_isolation,
    emit_delegation_evidence,
    revoke_delegation,
)

ALL_WORKFLOWS = [DelegateTenantWorkflow]
ALL_ACTIVITIES = [
    create_child_topology,
    bind_child_identifiers,
    determine_connector_mode,
    apply_shared_connector_delegation,
    apply_trust_scope,
    verify_tenant_isolation,
    emit_delegation_evidence,
    revoke_delegation,
]

WorkflowClass = DelegateTenantWorkflow
StartInput = DelegationStartInput
Result = DelegationResult
StatusQuery = DelegationStatusQuery
manifest = MANIFEST
definition = build_definition(
    api_module_name=__name__,
    manifest=MANIFEST,
    start_input_type=DelegationStartInput,
    status_query_type=DelegationStatusQuery,
    workflow_types=ALL_WORKFLOWS,
    activity_functions=ALL_ACTIVITIES,
)


def register() -> None:
    """Backward-compatible hook for legacy callers."""
    from dataspace_control_plane_procedures.registry import _register_definition

    _register_definition(definition)


__all__ = [
    "DelegateTenantWorkflow",
    "MANIFEST",
    "WORKFLOW_TYPE",
    "TASK_QUEUE",
    "DelegationStartInput",
    "DelegationResult",
    "DelegationStatusQuery",
    "DelegationCarryState",
    "ConnectorModeDecided",
    "ApproveCrossBorderDelegation",
    "ApprovalResult",
    "RejectDelegation",
    "RejectionResult",
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
