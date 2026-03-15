from __future__ import annotations

from dataclasses import dataclass, field

from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState
from dataspace_control_plane_procedures._shared.compensation import CompensationLog
from dataspace_control_plane_procedures._shared.continue_as_new import DedupeState


@dataclass
class NegotiationWorkflowState:
    # preflight | credentials_checked | negotiation_started | awaiting_counterparty
    # | manual_review | agreement_concluded | transfer_authorized | expired | failed
    negotiation_state: str = "preflight"
    negotiation_ref: str = ""
    agreement_id: str = ""
    entitlement_id: str = ""
    transfer_auth_token: str = ""
    counterparty_response: str | None = None  # "accepted" | "rejected" | "counteroffer"
    pending_counteroffer_offer_id: str = ""
    pending_counteroffer_policy_id: str = ""
    manual_review: ManualReviewState = field(default_factory=ManualReviewState)
    compensation: CompensationLog = field(default_factory=CompensationLog)
    dedupe: DedupeState = field(default_factory=DedupeState)
    is_expired: bool = False
    iteration: int = 0
