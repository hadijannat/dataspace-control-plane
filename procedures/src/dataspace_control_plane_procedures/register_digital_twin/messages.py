from __future__ import annotations

from dataclasses import dataclass


# ── Update payloads ───────────────────────────────────────────────────────────

@dataclass
class ApproveSemanticMapping:
    reviewer_id: str
    confirmed_semantic_id: str


@dataclass
class SemanticApprovalResult:
    accepted: bool
