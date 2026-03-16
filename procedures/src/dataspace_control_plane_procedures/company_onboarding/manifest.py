from dataspace_control_plane_procedures._shared.manifests import ProcedureManifest
from dataspace_control_plane_procedures._shared.task_queues import ONBOARDING_QUEUE

WORKFLOW_TYPE = "CompanyOnboardingWorkflow"
TASK_QUEUE = ONBOARDING_QUEUE
WORKFLOW_ID_TEMPLATE = "company-onboarding:{tenant_id}:{legal_entity_id}"
SEARCH_ATTRIBUTE_KEYS = ("tenant_id", "legal_entity_id", "procedure_type", "status", "external_reference")
SUPPORTED_PACKS = ("catena-x", "gaia-x")
VERSION_MARKERS = ("company_onboarding.v2_hierarchy_phase",)

MANIFEST = ProcedureManifest(
    workflow_type=WORKFLOW_TYPE,
    task_queue=TASK_QUEUE,
    workflow_id_template=WORKFLOW_ID_TEMPLATE,
    search_attribute_keys=SEARCH_ATTRIBUTE_KEYS,
    supported_packs=SUPPORTED_PACKS,
    version_markers=VERSION_MARKERS,
    lifecycle="entity",
    conflict_policy="reject",
    supports_manual_review=True,
    supports_continue_as_new=True,
)
