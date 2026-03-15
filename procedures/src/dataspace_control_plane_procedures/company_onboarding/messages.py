from __future__ import annotations

from dataclasses import dataclass, field

# Re-export for convenience
from .input import OnboardingStatusQuery  # noqa: F401


@dataclass(frozen=True)
class ExternalApprovalEvent:
    """Signal: external approval callback from portal or registry."""
    event_id: str
    approved: bool
    notes: str = ""


@dataclass(frozen=True)
class MissingInfoSubmitted:
    """Signal: operator has submitted missing information to unblock the flow."""
    submission_id: str
    data: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ApproveCaseInput:
    """Update input: internal reviewer approves the case."""
    reviewer_id: str
    notes: str = ""


@dataclass(frozen=True)
class ApproveCaseResult:
    """Update result: confirmation of the approval decision."""
    accepted: bool
    review_id: str


@dataclass(frozen=True)
class RejectCaseInput:
    """Update input: internal reviewer rejects the case."""
    reviewer_id: str
    reason: str


@dataclass(frozen=True)
class RejectCaseResult:
    """Update result: confirmation of the rejection decision."""
    accepted: bool
