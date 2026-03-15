from dataclasses import dataclass, field

from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures._shared.compensation import CompensationLog
from dataspace_control_plane_procedures._shared.continue_as_new import DedupeState


@dataclass
class DelegationWorkflowState:
    # Phases: pending | child_topology_created | identifiers_bound |
    #         connector_mode_decided | trust_scope_ready | delegation_verified
    delegation_state: str = "pending"
    child_topology_ref: str = ""
    delegation_ref: str = ""
    connector_mode: str = ""              # "shared" | "dedicated"
    connector_ref: str = ""
    trust_scope_refs: list[str] = field(default_factory=list)
    manual_review: ManualReviewState = field(default_factory=ManualReviewState)
    compensation: CompensationLog = field(default_factory=CompensationLog)
    dedupe: DedupeState = field(default_factory=DedupeState)
    is_verified: bool = False
    is_rejected: bool = False
