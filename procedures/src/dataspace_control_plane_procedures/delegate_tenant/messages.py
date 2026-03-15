from __future__ import annotations

from dataclasses import dataclass

# Re-export for convenience
from .input import DelegationStatusQuery  # noqa: F401


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConnectorModeDecided:
    """Signal: operator overrides the auto connector-mode selection."""
    event_id: str
    mode: str                    # "shared" | "dedicated"
    connector_ref: str = ""


# ---------------------------------------------------------------------------
# Update inputs / results
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ApproveCrossBorderDelegation:
    """Update input: reviewer approves a pending cross-border delegation."""
    reviewer_id: str
    notes: str = ""


@dataclass(frozen=True)
class ApprovalResult:
    """Update result: confirmation of the cross-border approval."""
    accepted: bool


@dataclass(frozen=True)
class RejectDelegation:
    """Update input: reviewer rejects the delegation."""
    reviewer_id: str
    reason: str = ""


@dataclass(frozen=True)
class RejectionResult:
    """Update result: confirmation of the rejection decision."""
    accepted: bool
