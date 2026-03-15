from __future__ import annotations

from dataclasses import dataclass, field

from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures._shared.compensation import CompensationLog
from dataspace_control_plane_procedures._shared.continue_as_new import DedupeState


@dataclass
class WalletWorkflowState:
    # wallet_requested | did_ready | verification_methods_ready | credential_request_sent
    # | credential_issued | presentation_verified | bound_to_connector
    wallet_state: str = "wallet_requested"
    wallet_ref: str = ""
    wallet_did: str = ""
    credential_ids: list[str] = field(default_factory=list)
    issuer_endpoint: str = ""
    is_bound_to_connector: bool = False
    manual_review: ManualReviewState = field(default_factory=ManualReviewState)
    compensation: CompensationLog = field(default_factory=CompensationLog)
    dedupe: DedupeState = field(default_factory=DedupeState)
