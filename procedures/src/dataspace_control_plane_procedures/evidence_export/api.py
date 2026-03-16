from dataspace_control_plane_procedures.registry import build_definition

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

WorkflowClass = EvidenceExportWorkflow
StartInput = EvidenceExportStartInput
Result = EvidenceExportResult
StatusQuery = EvidenceExportStatusQuery
manifest = MANIFEST
definition = build_definition(
    api_module_name=__name__,
    manifest=MANIFEST,
    start_input_type=EvidenceExportStartInput,
    status_query_type=EvidenceExportStatusQuery,
    workflow_types=ALL_WORKFLOWS,
    activity_functions=ALL_ACTIVITIES,
)


def register() -> None:
    from dataspace_control_plane_procedures.registry import _register_definition

    _register_definition(definition)


__all__ = [
    "EvidenceExportWorkflow",
    "MANIFEST",
    "WORKFLOW_TYPE",
    "TASK_QUEUE",
    "EvidenceExportStartInput",
    "EvidenceExportResult",
    "EvidenceExportStatusQuery",
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
