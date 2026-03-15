from __future__ import annotations
from dataclasses import dataclass
from dataspace_control_plane_core.canonical_models.policy import ConstraintExpression


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
