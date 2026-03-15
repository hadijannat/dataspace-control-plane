from dataclasses import dataclass, field

from dataspace_control_plane_procedures._shared.compensation import CompensationLog
from dataspace_control_plane_procedures._shared.continue_as_new import DedupeState


@dataclass
class RotationWorkflowState:
    # Phases: scan_started | replacement_requested | replacement_verified |
    #         bindings_updated | old_credentials_retired
    rotation_state: str = "scan_started"
    expiring_credential_ids: list[str] = field(default_factory=list)
    new_credential_ids: list[str] = field(default_factory=list)
    rotated_count: int = 0
    is_paused: bool = False
    force_rotate_requested: bool = False
    last_rotation_at: str = ""
    compensation: CompensationLog = field(default_factory=CompensationLog)
    dedupe: DedupeState = field(default_factory=DedupeState)
    iteration: int = 0
