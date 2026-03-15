from .workflow import EvidenceExportWorkflow
from .manifest import MANIFEST, WORKFLOW_TYPE, TASK_QUEUE
from .input import EvidenceExportStartInput, EvidenceExportResult, EvidenceExportStatusQuery
from .activities import (
    collect_evidence_refs,
    build_manifest,
    request_kms_signature,
    store_bundle,
    publish_bundle_notification,
    dry_run_comparison,
)


ALL_WORKFLOWS = [EvidenceExportWorkflow]
ALL_ACTIVITIES = [
    collect_evidence_refs,
    build_manifest,
    request_kms_signature,
    store_bundle,
    publish_bundle_notification,
    dry_run_comparison,
]


def register() -> None:
    from dataspace_control_plane_procedures.registry import _register
    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


__all__ = [
    "EvidenceExportWorkflow",
    "MANIFEST",
    "WORKFLOW_TYPE",
    "TASK_QUEUE",
    "EvidenceExportStartInput",
    "EvidenceExportResult",
    "EvidenceExportStatusQuery",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "register",
]
