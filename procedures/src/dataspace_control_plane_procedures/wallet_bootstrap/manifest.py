from dataspace_control_plane_procedures._shared.manifests import ProcedureManifest
from dataspace_control_plane_procedures._shared.task_queues import MACHINE_TRUST_QUEUE

WORKFLOW_TYPE = "WalletBootstrapWorkflow"
TASK_QUEUE = MACHINE_TRUST_QUEUE
WORKFLOW_ID_TEMPLATE = "wallet:{tenant_id}:{legal_entity_id}:{wallet_profile}"
SEARCH_ATTRIBUTE_KEYS = ("tenant_id", "legal_entity_id", "procedure_type", "status")
SUPPORTED_PACKS = ("catena-x",)
VERSION_MARKERS: tuple[str, ...] = ()

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
    supports_continue_as_new=False,
)
