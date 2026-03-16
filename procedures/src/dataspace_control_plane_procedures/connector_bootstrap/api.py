"""Public exports for connector_bootstrap procedure."""
from dataspace_control_plane_procedures.registry import build_definition

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
definition = build_definition(
    api_module_name=__name__,
    manifest=MANIFEST,
    start_input_type=ConnectorStartInput,
    status_query_type=ConnectorStatusQuery,
    workflow_types=ALL_WORKFLOWS,
    activity_functions=ALL_ACTIVITIES,
)


def register() -> None:
    """Backward-compatible hook for legacy callers."""
    from dataspace_control_plane_procedures.registry import _register_definition

    _register_definition(definition)


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
    "definition",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "register",
]
