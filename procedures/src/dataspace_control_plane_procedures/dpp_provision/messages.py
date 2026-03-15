from __future__ import annotations

from dataclasses import dataclass, field


# ── Update payloads ───────────────────────────────────────────────────────────

@dataclass
class ApproveMandatoryFieldsReview:
    """Human reviewer approves the mandatory fields review, optionally providing overrides."""
    reviewer_id: str
    field_overrides: dict[str, str] = field(default_factory=dict)


@dataclass
class ApproveResult:
    accepted: bool
