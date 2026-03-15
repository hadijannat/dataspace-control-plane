from __future__ import annotations
from dataclasses import dataclass, field

HISTORY_THRESHOLD = 9_000   # Warn at 10,240; terminate at 51,200


def should_continue_as_new(
    event_count: int,
    threshold: int = HISTORY_THRESHOLD,
) -> bool:
    return event_count >= threshold


@dataclass
class DedupeState:
    """Rolling set of handled message/idempotency IDs, carried across Continue-As-New."""
    _handled: set[str] = field(default_factory=set)
    max_size: int = 500

    def is_duplicate(self, msg_id: str) -> bool:
        return msg_id in self._handled

    def mark_handled(self, msg_id: str) -> None:
        if len(self._handled) >= self.max_size:
            # Evict oldest half (simple trim — real impl should use LRU)
            items = list(self._handled)
            self._handled = set(items[len(items) // 2 :])
        self._handled.add(msg_id)

    def snapshot(self) -> set[str]:
        return set(self._handled)

    @classmethod
    def from_snapshot(cls, snapshot: set[str], max_size: int = 500) -> "DedupeState":
        obj = cls(max_size=max_size)
        obj._handled = set(snapshot)
        return obj
