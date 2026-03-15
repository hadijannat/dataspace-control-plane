from dataspace_control_plane_procedures._shared.manifests import ProcedureManifest
from dataspace_control_plane_procedures._shared.task_queues import CONTRACTS_NEGOTIATION_QUEUE

WORKFLOW_TYPE = "NegotiateContractWorkflow"
TASK_QUEUE = CONTRACTS_NEGOTIATION_QUEUE
WORKFLOW_ID_TEMPLATE = "contract:{tenant_id}:{counterparty_connector_id}:{offer_id}:{purpose}"

MANIFEST = ProcedureManifest(
    workflow_type=WORKFLOW_TYPE,
    task_queue=TASK_QUEUE,
    workflow_id_template=WORKFLOW_ID_TEMPLATE,
    search_attribute_keys=("tenant_id", "legal_entity_id", "procedure_type", "status", "agreement_id", "asset_id"),
    lifecycle="entity",
    conflict_policy="use_existing",
    supports_manual_review=True,
    supports_continue_as_new=True,
)
