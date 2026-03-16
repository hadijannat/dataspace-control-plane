"""Public API surface for the publish_asset procedure."""
from __future__ import annotations

from dataspace_control_plane_procedures.registry import build_definition

from dataspace_control_plane_procedures.publish_asset.workflow import PublishAssetWorkflow
from dataspace_control_plane_procedures.publish_asset.input import (
    PublishAssetResult,
    PublishAssetStartInput,
    PublishAssetStatusQuery,
)
from dataspace_control_plane_procedures.publish_asset.messages import (
    ForceRepublish,
    ForceRepublishResult,
)
from dataspace_control_plane_procedures.publish_asset.activities import ALL_ACTIVITIES
from dataspace_control_plane_procedures.publish_asset.manifest import MANIFEST, TASK_QUEUE, WORKFLOW_TYPE

ALL_WORKFLOWS = [PublishAssetWorkflow]
ALL_ACTIVITIES = ALL_ACTIVITIES  # re-export
WorkflowClass = PublishAssetWorkflow
StartInput = PublishAssetStartInput
Result = PublishAssetResult
StatusQuery = PublishAssetStatusQuery
manifest = MANIFEST
definition = build_definition(
    api_module_name=__name__,
    manifest=MANIFEST,
    start_input_type=PublishAssetStartInput,
    status_query_type=PublishAssetStatusQuery,
    workflow_types=ALL_WORKFLOWS,
    activity_functions=ALL_ACTIVITIES,
)


def register() -> None:
    """Side-effect registration into the global procedure registry."""
    from dataspace_control_plane_procedures.registry import _register_definition

    _register_definition(definition)


__all__ = [
    "PublishAssetWorkflow",
    "WORKFLOW_TYPE",
    "TASK_QUEUE",
    "PublishAssetStartInput",
    "PublishAssetResult",
    "PublishAssetStatusQuery",
    "ForceRepublish",
    "ForceRepublishResult",
    "WorkflowClass",
    "StartInput",
    "Result",
    "StatusQuery",
    "manifest",
    "definition",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "MANIFEST",
    "register",
]
