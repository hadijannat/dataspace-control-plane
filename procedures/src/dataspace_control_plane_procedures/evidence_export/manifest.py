from dataspace_control_plane_procedures._shared.manifests import ProcedureManifest
from dataspace_control_plane_procedures._shared.task_queues import COMPLIANCE_QUEUE

WORKFLOW_TYPE = "EvidenceExportWorkflow"
TASK_QUEUE = COMPLIANCE_QUEUE
WORKFLOW_ID_TEMPLATE = "evidence-export:{tenant_id}:{scope}:{period_or_request_id}"
SEARCH_ATTRIBUTE_KEYS = ("tenant_id", "legal_entity_id", "procedure_type", "status")
SUPPORTED_PACKS: tuple[str, ...] = ()
VERSION_MARKERS: tuple[str, ...] = ()

MANIFEST = ProcedureManifest(
    workflow_type=WORKFLOW_TYPE,
    task_queue=TASK_QUEUE,
    workflow_id_template=WORKFLOW_ID_TEMPLATE,
    search_attribute_keys=SEARCH_ATTRIBUTE_KEYS,
    supported_packs=SUPPORTED_PACKS,
    version_markers=VERSION_MARKERS,
    lifecycle="one_shot",
    conflict_policy="reject",
    supports_manual_review=False,
    supports_continue_as_new=False,
)
