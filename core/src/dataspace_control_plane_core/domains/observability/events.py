"""Domain events for observability semantic changes."""
from __future__ import annotations

from dataclasses import dataclass

from dataspace_control_plane_core.domains._shared.events import DomainEvent


@dataclass(frozen=True)
class OperationalStatusRecorded(DomainEvent, event_type="observability.OperationalStatusRecorded"):
    status_code: str = ""
