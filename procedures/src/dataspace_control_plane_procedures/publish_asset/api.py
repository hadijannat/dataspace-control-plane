"""Public API surface for the publish_asset procedure."""
from __future__ import annotations

from dataspace_control_plane_procedures.publish_asset.workflow import PublishAssetWorkflow
from dataspace_control_plane_procedures.publish_asset.activities import ALL_ACTIVITIES
from dataspace_control_plane_procedures.publish_asset.manifest import MANIFEST, TASK_QUEUE

ALL_WORKFLOWS = [PublishAssetWorkflow]
ALL_ACTIVITIES = ALL_ACTIVITIES  # re-export


def register(workflow_registry: dict | None = None, activity_registry: dict | None = None) -> None:
    """Side-effect registration into the global procedure registry."""
    from dataspace_control_plane_procedures.registry import _register

    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


__all__ = [
    "PublishAssetWorkflow",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "MANIFEST",
    "register",
]
