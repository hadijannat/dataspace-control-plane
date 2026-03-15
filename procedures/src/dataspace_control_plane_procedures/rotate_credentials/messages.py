from __future__ import annotations

from dataclasses import dataclass

# Re-export for convenience
from .input import RotationStatusQuery  # noqa: F401


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ForceRotate:
    """Signal: trigger an immediate rotation cycle, bypassing the scheduled timer."""
    event_id: str
    reason: str = ""


# ---------------------------------------------------------------------------
# Update inputs / results
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PauseRotation:
    """Update input: pause future rotation iterations."""
    reviewer_id: str


@dataclass(frozen=True)
class PauseResult:
    """Update result: confirmation that rotation has been paused."""
    accepted: bool


@dataclass(frozen=True)
class ResumeRotation:
    """Update input: resume paused rotation."""
    reviewer_id: str
    notes: str = ""


@dataclass(frozen=True)
class ResumeResult:
    """Update result: confirmation that rotation has been resumed."""
    accepted: bool
