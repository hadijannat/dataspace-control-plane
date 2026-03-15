from dataspace_control_plane_procedures._shared.manifests import ProcedureManifest
from dataspace_control_plane_procedures._shared.task_queues import ONBOARDING_QUEUE

WORKFLOW_TYPE = "ConnectorBootstrapWorkflow"
TASK_QUEUE = ONBOARDING_QUEUE
WORKFLOW_ID_TEMPLATE = "connector:{tenant_id}:{legal_entity_id}:{environment}:{binding_name}"
SEARCH_ATTRIBUTE_KEYS = ("tenant_id", "legal_entity_id", "procedure_type", "status", "external_reference")
SUPPORTED_PACKS = ("catena-x",)
VERSION_MARKERS = ("connector_bootstrap.v2_health_check",)

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
