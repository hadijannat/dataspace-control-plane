from dataspace_control_plane_procedures.registry import build_definition

from .workflow import RevokeCredentialsWorkflow
from .manifest import MANIFEST, WORKFLOW_TYPE, TASK_QUEUE
from .input import RevocationStartInput, RevocationResult, RevocationStatusQuery
from .messages import ExternalRevocationConfirmed
from .activities import (
    update_credential_status,
    propagate_to_connector_bindings,
    find_dependent_procedures,
    notify_dependent_procedures,
    freeze_dependent_procedures,
    record_revocation_evidence,
)


ALL_WORKFLOWS = [RevokeCredentialsWorkflow]
ALL_ACTIVITIES = [
    update_credential_status,
    propagate_to_connector_bindings,
    find_dependent_procedures,
    notify_dependent_procedures,
    freeze_dependent_procedures,
    record_revocation_evidence,
]

WorkflowClass = RevokeCredentialsWorkflow
StartInput = RevocationStartInput
Result = RevocationResult
StatusQuery = RevocationStatusQuery
manifest = MANIFEST
definition = build_definition(
    api_module_name=__name__,
    manifest=MANIFEST,
    start_input_type=RevocationStartInput,
    status_query_type=RevocationStatusQuery,
    workflow_types=ALL_WORKFLOWS,
    activity_functions=ALL_ACTIVITIES,
)


def register() -> None:
    from dataspace_control_plane_procedures.registry import _register_definition

    _register_definition(definition)


__all__ = [
    "RevokeCredentialsWorkflow",
    "MANIFEST",
    "WORKFLOW_TYPE",
    "TASK_QUEUE",
    "RevocationStartInput",
    "RevocationResult",
    "RevocationStatusQuery",
    "ExternalRevocationConfirmed",
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
