from dataclasses import dataclass, field
from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures._shared.compensation import CompensationLog
from dataspace_control_plane_procedures._shared.continue_as_new import DedupeState


@dataclass
class OnboardingWorkflowState:
    phase: str = "pending"
    registration_ref: str = ""
    approval_ref: str = ""
    bpnl: str = ""
    wallet_ref: str = ""
    connector_ref: str = ""
    compliance_ref: str = ""
    manual_review: ManualReviewState = field(default_factory=ManualReviewState)
    compensation: CompensationLog = field(default_factory=CompensationLog)
    dedupe: DedupeState = field(default_factory=DedupeState)
    iteration: int = 0
    error_reason: str = ""
    is_cancelled: bool = False
