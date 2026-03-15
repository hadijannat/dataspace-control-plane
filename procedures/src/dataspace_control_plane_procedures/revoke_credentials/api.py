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


def register() -> None:
    from dataspace_control_plane_procedures.registry import _register
    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


__all__ = [
    "RevokeCredentialsWorkflow",
    "MANIFEST",
    "WORKFLOW_TYPE",
    "TASK_QUEUE",
    "RevocationStartInput",
    "RevocationResult",
    "RevocationStatusQuery",
    "ExternalRevocationConfirmed",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "register",
]
