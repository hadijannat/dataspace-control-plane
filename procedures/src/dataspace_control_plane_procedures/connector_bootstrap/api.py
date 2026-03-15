"""Public exports for connector_bootstrap procedure."""
from .workflow import ConnectorBootstrapWorkflow
from .manifest import MANIFEST, WORKFLOW_TYPE, TASK_QUEUE
from .input import ConnectorStartInput, ConnectorResult, ConnectorStatusQuery, ConnectorCarryState
from .messages import HealthDegraded, WalletBound, ForceHealthCheckInput, ForceHealthCheckResult
from .activities import (
    plan_connector_infra,
    apply_connector_infra,
    wait_for_runtime_healthy,
    link_wallet_to_connector,
    register_in_dataspace,
    verify_discovery,
    decommission_connector,
)

ALL_WORKFLOWS = [ConnectorBootstrapWorkflow]
ALL_ACTIVITIES = [
    plan_connector_infra,
    apply_connector_infra,
    wait_for_runtime_healthy,
    link_wallet_to_connector,
    register_in_dataspace,
    verify_discovery,
    decommission_connector,
]

WorkflowClass = ConnectorBootstrapWorkflow
StartInput = ConnectorStartInput
Result = ConnectorResult
StatusQuery = ConnectorStatusQuery
manifest = MANIFEST


def register() -> None:
    """Called by registry.populate_from_procedures() at worker startup."""
    from dataspace_control_plane_procedures.registry import _register
    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


__all__ = [
    "ConnectorBootstrapWorkflow",
    "MANIFEST",
    "WORKFLOW_TYPE",
    "TASK_QUEUE",
    "ConnectorStartInput",
    "ConnectorResult",
    "ConnectorStatusQuery",
    "ConnectorCarryState",
    "HealthDegraded",
    "WalletBound",
    "ForceHealthCheckInput",
    "ForceHealthCheckResult",
    "WorkflowClass",
    "StartInput",
    "Result",
    "StatusQuery",
    "manifest",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "register",
]
