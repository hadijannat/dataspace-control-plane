from __future__ import annotations

from dataclasses import dataclass


# ── Update payloads ───────────────────────────────────────────────────────────

@dataclass
class ForceRepublish:
    reviewer_id: str
    reason: str


@dataclass
class ForceRepublishResult:
    accepted: bool
