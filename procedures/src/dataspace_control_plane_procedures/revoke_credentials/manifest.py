from dataspace_control_plane_procedures._shared.manifests import ProcedureManifest
from dataspace_control_plane_procedures._shared.task_queues import MACHINE_TRUST_QUEUE

WORKFLOW_TYPE = "RevokeCredentialsWorkflow"
TASK_QUEUE = MACHINE_TRUST_QUEUE
WORKFLOW_ID_TEMPLATE = "revoke-credentials:{tenant_id}:{subject}:{credential_id}"

MANIFEST = ProcedureManifest(
    workflow_type=WORKFLOW_TYPE,
    task_queue=TASK_QUEUE,
    workflow_id_template=WORKFLOW_ID_TEMPLATE,
    search_attribute_keys=("tenant_id", "legal_entity_id", "procedure_type", "status"),
    lifecycle="one_shot",
    conflict_policy="reject",
    supports_manual_review=False,
    supports_continue_as_new=False,
)
