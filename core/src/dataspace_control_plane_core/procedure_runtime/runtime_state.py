"""Canonical runtime-state contract shared across apps and procedures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from dataspace_control_plane_core.domains._shared.time import utc_now

from .workflow_contracts import ProcedureStatus


@dataclass(frozen=True)
class ProcedureRuntimeState:
    """Workflow-engine-neutral runtime snapshot for a procedure execution."""

    status: ProcedureStatus
    phase: str = ""
    updated_at: datetime = field(default_factory=utc_now)
    failure_message: str = ""
    progress_percent: int = 0
    search_attributes: dict[str, Any] = field(default_factory=dict, hash=False)
    links: dict[str, str] = field(default_factory=dict, hash=False)

