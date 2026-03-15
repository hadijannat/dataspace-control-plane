"""Progress reporting models for long-running procedures."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcedureProgress:
    current_step: str = ""
    completed_steps: int = 0
    total_steps: int = 0
    message: str = ""

    @property
    def percent_complete(self) -> int:
        if self.total_steps <= 0:
            return 0
        return int((self.completed_steps / self.total_steps) * 100)
