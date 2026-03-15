"""Manufacturing-X RequirementProvider.

Combines the discovery and access/usage control rule sets into a single
provider that the registry exposes as the pack's RequirementProvider
capability.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .._shared.rule_model import RuleDefinition, ValidationResult
from .access_usage_rules import MxAccessUsageRules
from .discovery_rules import MxDiscoveryRules


class MxRequirementProvider:
    """RequirementProvider combining all Manufacturing-X normative rules.

    Delegates to :class:`MxDiscoveryRules` and :class:`MxAccessUsageRules`
    for rule emission and subject validation.
    """

    def __init__(self) -> None:
        self._discovery = MxDiscoveryRules()
        self._access_usage = MxAccessUsageRules()

    # ------------------------------------------------------------------
    # RequirementProvider interface
    # ------------------------------------------------------------------

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return all active MX requirements for ``context`` on ``on``."""
        rules: list[RuleDefinition] = []
        rules.extend(self._discovery.requirements(context=context, on=on))
        rules.extend(self._access_usage.requirements(context=context, on=on))
        return rules

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate ``subject`` against all active MX requirements.

        Violations from discovery and access/usage rules are merged into a
        single :class:`ValidationResult`.
        """
        subject_id = str(subject.get("id", "unknown"))
        result = ValidationResult(subject_id=subject_id)

        disc = self._discovery.validate(subject, context=context, on=on)
        for v in disc.violations:
            result.add(v)

        access = self._access_usage.validate(subject, context=context, on=on)
        for v in access.violations:
            result.add(v)

        return result
