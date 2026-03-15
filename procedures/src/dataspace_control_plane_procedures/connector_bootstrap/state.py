from dataclasses import dataclass, field
from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures._shared.compensation import CompensationLog
from dataspace_control_plane_procedures._shared.continue_as_new import DedupeState


@dataclass
class ConnectorWorkflowState:
    # Lifecycle states: desired → plan_ready → infra_applied → runtime_healthy
    #                   → wallet_linked → dataspace_registered → discovery_verified
    #                   | degraded (can arrive from runtime_healthy onward)
    connector_state: str = "desired"
    connector_binding_id: str = ""
    dataspace_connector_id: str = ""
    discovery_endpoint: str = ""
    plan_ref: str = ""
    infra_apply_ref: str = ""
    wallet_linked: bool = False
    dataspace_registered: bool = False
    last_health_check: str = ""
    manual_review: ManualReviewState = field(default_factory=ManualReviewState)
    compensation: CompensationLog = field(default_factory=CompensationLog)
    dedupe: DedupeState = field(default_factory=DedupeState)
    iteration: int = 0
    error_reason: str = ""
