from dataspace_control_plane_procedures._shared.manifests import ProcedureManifest
from dataspace_control_plane_procedures._shared.task_queues import CONTRACTS_NEGOTIATION_QUEUE

WORKFLOW_TYPE = "NegotiateContractWorkflow"
TASK_QUEUE = CONTRACTS_NEGOTIATION_QUEUE
WORKFLOW_ID_TEMPLATE = "contract:{tenant_id}:{counterparty_connector_id}:{offer_id}:{purpose}"
SEARCH_ATTRIBUTE_KEYS = ("tenant_id", "legal_entity_id", "procedure_type", "status", "agreement_id", "asset_id")
SUPPORTED_PACKS = ("catena-x", "gaia-x")
VERSION_MARKERS = ("negotiate_contract.v2_counteroffer",)

MANIFEST = ProcedureManifest(
    workflow_type=WORKFLOW_TYPE,
    task_queue=TASK_QUEUE,
    workflow_id_template=WORKFLOW_ID_TEMPLATE,
    search_attribute_keys=SEARCH_ATTRIBUTE_KEYS,
    supported_packs=SUPPORTED_PACKS,
    version_markers=VERSION_MARKERS,
    lifecycle="entity",
    conflict_policy="use_existing",
    supports_manual_review=True,
    supports_continue_as_new=True,
)
