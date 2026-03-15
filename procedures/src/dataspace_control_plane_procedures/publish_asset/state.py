from __future__ import annotations

from dataclasses import dataclass, field

from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures._shared.compensation import CompensationLog


@dataclass
class PublishAssetWorkflowState:
    # pending | snapshot_fetched | source_ready | policy_compiled | published
    # | visibility_verified | evidence_recorded
    phase: str = "pending"
    mapping_snapshot_id: str = ""
    compiled_policy_id: str = ""
    asset_offer_id: str = ""
    discoverability_url: str = ""
    evidence_ref: str = ""
    manual_review: ManualReviewState = field(default_factory=ManualReviewState)
    compensation: CompensationLog = field(default_factory=CompensationLog)
