"""
Canonical policy AST — internal normalized representation of ODRL policies.
Do not store raw JSON-LD. Normalize at the adapter boundary, evaluate here.
"""
from __future__ import annotations
from typing import Any, Literal
from pydantic import field_validator

from .common import CanonicalBase
from .enums import PolicyEffect


class PartyRef(CanonicalBase):
    """Reference to a policy party (issuer, assigner, assignee)."""
    id: str  # DID or BPN or placeholder
    role: Literal["assigner", "assignee", "any"] = "any"


class ConstraintExpression(CanonicalBase):
    """A single ODRL constraint: left_operand operator right_operand."""
    left_operand: str   # e.g. "cx:UsagePurpose"
    operator: str       # e.g. "eq", "lteq", "isPartOf"
    right_operand: Any
    unit: str | None = None


class Duty(CanonicalBase):
    """An obligation or duty within a permission/prohibition."""
    action: str
    constraints: list[ConstraintExpression] = []
    target: str | None = None


class PolicyRule(CanonicalBase):
    """Base for permission/prohibition/obligation rules."""
    effect: PolicyEffect
    action: str
    target: str | None = None
    assignee: PartyRef | None = None
    assigner: PartyRef | None = None
    constraints: list[ConstraintExpression] = []
    duties: list[Duty] = []


class PermissionRule(PolicyRule):
    effect: PolicyEffect = PolicyEffect.PERMIT


class ProhibitionRule(PolicyRule):
    effect: PolicyEffect = PolicyEffect.PROHIBIT


class ObligationRule(PolicyRule):
    effect: PolicyEffect = PolicyEffect.OBLIGATE


class PolicyParseLoss(CanonicalBase):
    """Records a clause that could not be fully normalized during inbound parsing."""
    original_json: str
    reason: str
    field_path: str | None = None


class PolicyCompileWarning(CanonicalBase):
    """Warning emitted during outbound compilation to a target dialect."""
    rule_index: int
    message: str
    target_dialect: str


class CanonicalPolicy(CanonicalBase):
    """
    Internal normalized policy representation.
    Parsed from ODRL/JSON-LD; compiled back to dialect for EDC/DSP wire format.
    """
    policy_id: str
    version: str = "1"
    permissions: list[PermissionRule] = []
    prohibitions: list[ProhibitionRule] = []
    obligations: list[ObligationRule] = []
    parse_losses: list[PolicyParseLoss] = []
    compile_warnings: list[PolicyCompileWarning] = []
    needs_review: bool = False

    def has_losses(self) -> bool:
        return bool(self.parse_losses)
