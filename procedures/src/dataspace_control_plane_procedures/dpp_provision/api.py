"""Public exports for dpp_provision procedure."""
from dataspace_control_plane_procedures.registry import build_definition

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

WorkflowClass = DppProvisionWorkflow
StartInput = DppStartInput
Result = DppResult
StatusQuery = DppStatusQuery
manifest = MANIFEST
definition = build_definition(
    api_module_name=__name__,
    manifest=MANIFEST,
    start_input_type=DppStartInput,
    status_query_type=DppStatusQuery,
    workflow_types=ALL_WORKFLOWS,
    activity_functions=ALL_ACTIVITIES,
)


def register() -> None:
    from dataspace_control_plane_procedures.registry import _register_definition

    _register_definition(definition)


__all__ = [
    "DppProvisionWorkflow", "MANIFEST", "WORKFLOW_TYPE", "TASK_QUEUE",
    "DppStartInput", "DppResult", "DppStatusQuery",
    "ApproveMandatoryFieldsReview", "ApproveResult",
    "WorkflowClass", "StartInput", "Result", "StatusQuery", "manifest", "definition",
    "ALL_WORKFLOWS", "ALL_ACTIVITIES", "register",
]
