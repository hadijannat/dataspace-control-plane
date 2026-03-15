from __future__ import annotations

from dataclasses import dataclass, field

from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures._shared.compensation import CompensationLog


@dataclass
class DppWorkflowState:
    # pending | source_snapshot_taken | mandatory_data_resolved | submodels_compiled
    # | passport_registered | id_link_bound | published | evidence_recorded
    phase: str = "pending"
    source_snapshot_ref: str = ""
    submodel_ids: list[str] = field(default_factory=list)
    dpp_id: str = ""
    identifier_link: str = ""
    completeness_score: float = 0.0
    evidence_ref: str = ""
    missing_mandatory: list[str] = field(default_factory=list)
    field_overrides: dict[str, str] = field(default_factory=dict)
    manual_review: ManualReviewState = field(default_factory=ManualReviewState)
    compensation: CompensationLog = field(default_factory=CompensationLog)
