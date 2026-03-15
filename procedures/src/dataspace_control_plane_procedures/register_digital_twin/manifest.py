from dataspace_control_plane_procedures._shared.manifests import ProcedureManifest
from dataspace_control_plane_procedures._shared.task_queues import TWINS_PUBLICATION_QUEUE

WORKFLOW_TYPE = "RegisterDigitalTwinWorkflow"
TASK_QUEUE = TWINS_PUBLICATION_QUEUE
WORKFLOW_ID_TEMPLATE = "register-twin:{tenant_id}:{aas_id}:{revision}"

MANIFEST = ProcedureManifest(
    workflow_type=WORKFLOW_TYPE,
    task_queue=TASK_QUEUE,
    workflow_id_template=WORKFLOW_ID_TEMPLATE,
    search_attribute_keys=("tenant_id", "legal_entity_id", "procedure_type", "status", "asset_id"),
    lifecycle="one_shot",
    conflict_policy="reject",
    supports_manual_review=True,
    supports_continue_as_new=False,
)
