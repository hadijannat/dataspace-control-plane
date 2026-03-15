"""Catena-X combined requirement provider.

Aggregates topology and governance rules into a single RequirementProvider
that callers can treat as the authoritative Catena-X rule set.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .._shared.rule_model import RuleDefinition, ValidationResult
from .governance import CatenaxGovernanceValidator
from .topology_rules import CatenaxTopologyValidator


class CatenaxRequirementProvider:
    """RequirementProvider combining topology and governance rules.

    Callers receive a unified view of all active Catena-X requirements
    without needing to know the internal split between topology and
    governance validators.
    """

    def __init__(self) -> None:
        self._topology = CatenaxTopologyValidator()
        self._governance = CatenaxGovernanceValidator()

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return all active Catena-X requirements on ``on``."""
        topology_rules = self._topology.requirements(context=context, on=on)
        governance_rules = self._governance.requirements(context=context, on=on)
        seen: set[str] = set()
        combined: list[RuleDefinition] = []
        for rule in topology_rules + governance_rules:
            if rule.rule_id not in seen:
                seen.add(rule.rule_id)
                combined.append(rule)
        return combined

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Run both topology and governance validators and union all violations."""
        topology_result = self._topology.validate(subject, context=context, on=on)
        governance_result = self._governance.validate(subject, context=context, on=on)

        subject_id = (
            subject.get("bpnl") or subject.get("id") or "unknown"
        )
        combined = ValidationResult(subject_id=str(subject_id))
        for violation in topology_result.violations + governance_result.violations:
            combined.add(violation)
        return combined
