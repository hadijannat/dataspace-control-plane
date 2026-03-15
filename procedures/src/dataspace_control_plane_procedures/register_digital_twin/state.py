from __future__ import annotations

from dataclasses import dataclass, field

from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures._shared.compensation import CompensationLog


@dataclass
class TwinWorkflowState:
    # pending | validated | shell_upserted | submodels_upserted | registry_registered
    # | access_bound | verification_passed
    phase: str = "pending"
    shell_id: str = ""
    submodel_ids: list[str] = field(default_factory=list)
    registry_url: str = ""
    access_rule_ids: list[str] = field(default_factory=list)
    evidence_ref: str = ""
    manual_review: ManualReviewState = field(default_factory=ManualReviewState)
    compensation: CompensationLog = field(default_factory=CompensationLog)
