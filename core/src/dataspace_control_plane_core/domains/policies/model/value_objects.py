from __future__ import annotations
from dataclasses import dataclass
from dataspace_control_plane_core.canonical_models.policy import ConstraintExpression, Duty as CanonicalDuty


@dataclass(frozen=True)
class PurposeCode:
    code: str
    namespace: str  # e.g. "cx", "gaia-x", "custom"
    description: str | None = None

    def full_uri(self) -> str:
        return f"{self.namespace}:{self.code}"


@dataclass(frozen=True)
class LossyClause:
    """A policy clause that could not be fully normalized — preserved verbatim."""
    original_json: str
    reason: str
    field_path: str | None = None


Constraint = ConstraintExpression
Duty = CanonicalDuty


@dataclass(frozen=True)
class PolicyOffer:
    offer_id: str
    policy_id: str
    purpose: PurposeCode | None = None
    needs_review: bool = False


@dataclass(frozen=True)
class PolicyParseReport:
    parse_losses: tuple[LossyClause, ...] = ()
    needs_review: bool = False
