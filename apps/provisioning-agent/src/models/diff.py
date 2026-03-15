"""
Diff model: the result of comparing desired vs actual state.
Each change has a human-readable description and a severity (safe/review/destructive).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeSeverity(str, Enum):
    SAFE = "safe"         # Can apply without extra confirmation
    REVIEW = "review"     # Should be reviewed before applying
    DESTRUCTIVE = "destructive"  # Requires explicit --force flag


@dataclass
class StateChange:
    resource_type: str
    resource_id: str
    operation: str  # "create", "update", "delete", "noop"
    severity: ChangeSeverity
    description: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class StateDiff:
    changes: list[StateChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(c.operation != "noop" for c in self.changes)

    @property
    def has_destructive(self) -> bool:
        return any(c.severity == ChangeSeverity.DESTRUCTIVE for c in self.changes)

    def summary(self) -> str:
        ops: dict[str, int] = {}
        for c in self.changes:
            ops[c.operation] = ops.get(c.operation, 0) + 1
        return " | ".join(f"{op}: {count}" for op, count in ops.items())
