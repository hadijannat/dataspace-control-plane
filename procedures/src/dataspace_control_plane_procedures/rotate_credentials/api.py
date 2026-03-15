"""Public exports for the rotate_credentials procedure.

Import this module to get everything needed to run or interact with the
RotateCredentialsWorkflow.  Call register() at worker startup to wire all
workflows and activities into the procedure registry.
"""
from __future__ import annotations

from .workflow import RotateCredentialsWorkflow
from .manifest import MANIFEST, TASK_QUEUE, WORKFLOW_TYPE
from .input import RotationCarryState, RotationResult, RotationStartInput, RotationStatusQuery
from .messages import ForceRotate, PauseResult, PauseRotation, ResumeResult, ResumeRotation
from .activities import (
    enumerate_expiring_credentials,
    request_credential_reissuance,
    retire_new_credentials_on_failure,
    retire_old_credentials,
    schedule_next_rotation,
    update_connector_wallet_bindings,
    verify_new_credential_presentation,
)

ALL_WORKFLOWS = [RotateCredentialsWorkflow]
ALL_ACTIVITIES = [
    enumerate_expiring_credentials,
    request_credential_reissuance,
    verify_new_credential_presentation,
    update_connector_wallet_bindings,
    retire_old_credentials,
    schedule_next_rotation,
    retire_new_credentials_on_failure,
]


def register() -> None:
    """Called by registry.populate_from_procedures() at worker startup.

    Registers all workflows and activities for the machine-trust task queue.
    """
    from dataspace_control_plane_procedures.registry import _register

    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


__all__ = [
    "RotateCredentialsWorkflow",
    "MANIFEST",
    "WORKFLOW_TYPE",
    "TASK_QUEUE",
    "RotationStartInput",
    "RotationResult",
    "RotationStatusQuery",
    "RotationCarryState",
    "ForceRotate",
    "PauseRotation",
    "PauseResult",
    "ResumeRotation",
    "ResumeResult",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "register",
    "enumerate_expiring_credentials",
    "request_credential_reissuance",
    "verify_new_credential_presentation",
    "update_connector_wallet_bindings",
    "retire_old_credentials",
    "schedule_next_rotation",
    "retire_new_credentials_on_failure",
]
