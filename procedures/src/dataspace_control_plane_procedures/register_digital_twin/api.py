"""Public exports for register_digital_twin procedure."""
from .workflow import RegisterDigitalTwinWorkflow
from .manifest import MANIFEST, WORKFLOW_TYPE, TASK_QUEUE
from .input import TwinStartInput, TwinResult, TwinStatusQuery
from .messages import ApproveSemanticMapping, SemanticApprovalResult
from .activities import (
    validate_canonical_shell, upsert_aas_shell, upsert_submodels,
    register_descriptor_in_registry, bind_access_rules,
    verify_readback_from_registry, record_twin_evidence, deregister_shell,
)

ALL_WORKFLOWS = [RegisterDigitalTwinWorkflow]
ALL_ACTIVITIES = [
    validate_canonical_shell, upsert_aas_shell, upsert_submodels,
    register_descriptor_in_registry, bind_access_rules,
    verify_readback_from_registry, record_twin_evidence, deregister_shell,
]

WorkflowClass = RegisterDigitalTwinWorkflow
StartInput = TwinStartInput
Result = TwinResult
StatusQuery = TwinStatusQuery
manifest = MANIFEST


def register() -> None:
    from dataspace_control_plane_procedures.registry import _register
    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


__all__ = [
    "RegisterDigitalTwinWorkflow", "MANIFEST", "WORKFLOW_TYPE", "TASK_QUEUE",
    "TwinStartInput", "TwinResult", "TwinStatusQuery",
    "ApproveSemanticMapping", "SemanticApprovalResult",
    "WorkflowClass", "StartInput", "Result", "StatusQuery", "manifest",
    "ALL_WORKFLOWS", "ALL_ACTIVITIES", "register",
]
