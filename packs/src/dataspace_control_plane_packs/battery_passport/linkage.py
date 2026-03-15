"""Predecessor/successor battery passport linkage.

When a battery is repurposed or remanufactured, a new passport must be
created and linked to the original via a typed predecessor/successor relation.
When a battery is recycled, its passport ceases entirely.

Reference: Regulation (EU) 2023/1542, Art. 74.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from .._shared.rule_model import RuleViolation, ValidationResult


@dataclass(frozen=True)
class PassportLink:
    """A typed link between two battery passports in the lifecycle chain."""

    predecessor_passport_id: str
    successor_passport_id: str
    link_type: Literal["repurposed", "remanufactured"]
    created_at: str
    """ISO 8601 UTC timestamp."""

    def as_dict(self) -> dict:
        return {
            "predecessor_passport_id": self.predecessor_passport_id,
            "successor_passport_id": self.successor_passport_id,
            "link_type": self.link_type,
            "created_at": self.created_at,
        }


SUCCESSOR_PASSPORT_REQUIRED = "battery:successor-passport-on-repurpose"
_REQUIRES_SUCCESSOR = {"repurposed", "remanufactured"}
_TERMINAL_STATE = "recycled_ceased"


def build_passport_link(
    predecessor_id: str,
    successor_id: str,
    link_type: Literal["repurposed", "remanufactured"],
) -> PassportLink:
    """Build a PassportLink with the current UTC timestamp."""
    return PassportLink(
        predecessor_passport_id=predecessor_id,
        successor_passport_id=successor_id,
        link_type=link_type,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def validate_linkage(subject: dict, current_state: str) -> ValidationResult:
    """Validate passport linkage requirements for the given lifecycle state.

    Rules:
    - If state is ``repurposed`` or ``remanufactured``: a ``successor_passport_id``
      is required in the subject.
    - If state is ``recycled_ceased``: no further linkage is needed (passport terminal).
    """
    result = ValidationResult(subject_id=subject.get("battery_id", "unknown"))
    if current_state in _REQUIRES_SUCCESSOR:
        if not subject.get("successor_passport_id"):
            result.add(RuleViolation(
                rule_id=SUCCESSOR_PASSPORT_REQUIRED,
                severity="error",
                message=(
                    f"Battery in state '{current_state}' must have a successor passport. "
                    "A new passport must be linked to the repurposed/remanufactured battery."
                ),
                context={"current_state": current_state},
            ))
    return result
