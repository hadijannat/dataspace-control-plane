"""Gaia-X requirement provider — aggregates baseline compliance rules."""
from __future__ import annotations

from datetime import date
from typing import Any

from .._shared.interfaces import RequirementProvider
from .._shared.rule_model import RuleDefinition, ValidationResult
from .baseline.compliance_rules import GaiaXComplianceValidator


class GaiaXRequirementProvider:
    """Implements RequirementProvider for the Gaia-X baseline trust framework.

    Delegates to the baseline compliance validator. Federation overlays
    may extend this by wrapping and augmenting the result.
    """

    def __init__(self) -> None:
        self._validator = GaiaXComplianceValidator()

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        return self._validator.requirements(context=context, on=on)

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        return self._validator.validate(subject, context=context, on=on)
