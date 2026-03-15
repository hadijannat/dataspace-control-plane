"""Manual review and approval primitives for procedures."""
from __future__ import annotations

from dataclasses import dataclass

from dataspace_control_plane_core.domains._shared.actor import ActorRef


@dataclass(frozen=True)
class ManualApproval:
    required: bool = False
    reason: str = ""
    approver: ActorRef | None = None
    comment: str = ""
