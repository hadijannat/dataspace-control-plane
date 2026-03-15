"""Public exports for delegate_tenant procedure."""
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


def register() -> None:
    """Called by registry.populate_from_procedures() at worker startup."""
    from dataspace_control_plane_procedures.registry import _register
    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


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
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "register",
]
