"""Public exports for dpp_provision procedure."""
from .workflow import DppProvisionWorkflow
from .manifest import MANIFEST, WORKFLOW_TYPE, TASK_QUEUE
from .input import DppStartInput, DppResult, DppStatusQuery
from .messages import ApproveMandatoryFieldsReview, ApproveResult
from .activities import (
    collect_source_snapshot, resolve_submodel_templates, compile_submodels,
    upsert_dpp_twin_data, bind_identifier_link, record_dpp_evidence, deregister_dpp,
)

ALL_WORKFLOWS = [DppProvisionWorkflow]
ALL_ACTIVITIES = [
    collect_source_snapshot, resolve_submodel_templates, compile_submodels,
    upsert_dpp_twin_data, bind_identifier_link, record_dpp_evidence, deregister_dpp,
]


def register() -> None:
    from dataspace_control_plane_procedures.registry import _register
    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


__all__ = [
    "DppProvisionWorkflow", "MANIFEST", "WORKFLOW_TYPE", "TASK_QUEUE",
    "DppStartInput", "DppResult", "DppStatusQuery",
    "ApproveMandatoryFieldsReview", "ApproveResult",
    "ALL_WORKFLOWS", "ALL_ACTIVITIES", "register",
]
