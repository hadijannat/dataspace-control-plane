from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime


@dataclass
class ManualReviewState:
    """Mutable in-workflow state for a pending human decision."""
    is_pending: bool = False
    review_id: str = ""
    blocking_reason: str = ""
    reviewer_id: str | None = None
    requested_at: datetime | None = None
    decided_at: datetime | None = None
    decision: str | None = None   # "approved" | "rejected"
    notes: str = ""

    def request(
        self,
        reason: str,
        review_id: str = "",
        *,
        requested_at: datetime | None = None,
    ) -> None:
        self.is_pending = True
        self.blocking_reason = reason
        self.review_id = review_id
        self.requested_at = requested_at
        self.decision = None
        self.decided_at = None

    def record_decision(
        self,
        decision: str,
        reviewer_id: str,
        notes: str = "",
        *,
        decided_at: datetime | None = None,
    ) -> None:
        self.is_pending = False
        self.decision = decision
        self.reviewer_id = reviewer_id
        self.notes = notes
        self.decided_at = decided_at

    def snapshot(self) -> "ManualReviewState":
        return replace(self)

    @classmethod
    def from_snapshot(cls, snapshot: "ManualReviewState | None") -> "ManualReviewState":
        if snapshot is None:
            return cls()
        return replace(snapshot)

    @property
    def is_approved(self) -> bool:
        return self.decision == "approved"

    @property
    def is_rejected(self) -> bool:
        return self.decision == "rejected"
