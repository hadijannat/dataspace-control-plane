from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CompensationMarker:
    action: str
    resource_id: str
    completed_at: datetime | None = None


@dataclass
class CompensationLog:
    """Append-only log of compensatable actions; drives rollback order."""
    _entries: list[CompensationMarker] = field(default_factory=list)

    def record(self, action: str, resource_id: str) -> None:
        self._entries.append(CompensationMarker(action=action, resource_id=resource_id))

    def pending(self) -> list[CompensationMarker]:
        """Return entries that have not been compensated, in reverse order."""
        return [e for e in reversed(self._entries) if e.completed_at is None]

    def mark_compensated(self, action: str, resource_id: str) -> None:
        for entry in self._entries:
            if entry.action == action and entry.resource_id == resource_id:
                entry.completed_at = datetime.now(timezone.utc)
                return
