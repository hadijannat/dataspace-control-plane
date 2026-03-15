"""ESPR DPP combined requirement provider.

Aggregates all core ESPR DPP rules (identifiers, data carriers, registry,
accessibility, backup) into a single RequirementProvider that the registry
can resolve by capability.

Reference: Regulation (EU) 2024/1781 (ESPR)
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .._shared.rule_model import RuleDefinition, ValidationResult
from .core_rules.accessibility import EsprAccessibilityValidator
from .core_rules.backup_copy import BackupCopyValidator
from .core_rules.data_carrier import DataCarrierValidator
from .core_rules.identifiers import EsprIdentifierValidator
from .core_rules.registry import RegistryValidator


class EsprRequirementProvider:
    """Combined RequirementProvider for all ESPR DPP core obligations.

    Delegates to the individual validators for identifiers, data carriers,
    registry registration, accessibility, and backup copy requirements.
    """

    def __init__(self) -> None:
        self._identifier = EsprIdentifierValidator()
        self._data_carrier = DataCarrierValidator()
        self._registry = RegistryValidator()
        self._accessibility = EsprAccessibilityValidator()
        self._backup = BackupCopyValidator()

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return all active ESPR DPP requirements applicable on ``on``."""
        rules: list[RuleDefinition] = []
        rules.extend(self._identifier.requirements(context=context, on=on))
        rules.extend(self._data_carrier.requirements(context=context, on=on))
        rules.extend(self._registry.requirements(context=context, on=on))
        rules.extend(self._accessibility.requirements(context=context, on=on))
        rules.extend(self._backup.requirements(context=context, on=on))
        return rules

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate ``subject`` against all active ESPR DPP requirements.

        Aggregates violations from all sub-validators. The ``subject_id`` of
        the returned result is taken from ``subject["product_id"]`` or "unknown".
        """
        product_id = subject.get("product_id", "unknown")
        result = ValidationResult(subject_id=str(product_id))

        for sub_result in [
            self._identifier.validate(subject, context=context, on=on),
            self._data_carrier.validate(subject, context=context, on=on),
            self._registry.validate(subject, context=context, on=on),
            self._accessibility.validate(subject, context=context, on=on),
            self._backup.validate(subject, context=context, on=on),
        ]:
            result.violations.extend(sub_result.violations)

        return result
