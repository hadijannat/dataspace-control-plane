"""Declarative rule object for all normative rules across all packs.

Every rule emitted by a pack must be traceable to an immutable normative source.
Rules are data — they carry no execution logic. Validators and compilers receive
rules and interpret them.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal, Mapping


@dataclass(frozen=True)
class RuleDefinition:
    """A single normative rule from a pack.

    Attributes:
        rule_id: Globally unique identifier, namespaced by pack
            (e.g. ``catenax:bpnl-required``, ``battery:annex-xiii:public-access``).
        title: Human-readable short title.
        severity: Blocking level: ``error`` = must pass; ``warning`` = flag only;
            ``info`` = informational.
        machine_checkable: True if this rule can be evaluated programmatically.
            False rules require human review.
        source_uri: Canonical URI of the authoritative document.
        source_version: Version/release of that document.
        effective_from: ISO 8601 date from which this rule applies. None = always.
        effective_to: ISO 8601 date until which this rule applies. None = indefinite.
        scope: Arbitrary key-value scope qualifiers (e.g. product group, battery type).
        payload: Rule-specific structured data — the actual machine-checkable content.
    """

    rule_id: str
    title: str
    severity: Literal["error", "warning", "info"]
    machine_checkable: bool
    source_uri: str
    source_version: str
    effective_from: date | None
    effective_to: date | None
    scope: dict[str, str]
    payload: Mapping[str, Any]

    def is_active(self, on: date | None = None) -> bool:
        """Return True if this rule is in effect on ``on`` (defaults to today)."""
        today = on or date.today()
        if self.effective_from and today < self.effective_from:
            return False
        if self.effective_to and today > self.effective_to:
            return False
        return True

    def fingerprint(self) -> str:
        """SHA-256 hex of the rule's stable identity fields.

        Used to detect rule identity changes across pack upgrades.
        """
        stable = {
            "rule_id": self.rule_id,
            "source_uri": self.source_uri,
            "source_version": self.source_version,
            "payload": dict(self.payload),
        }
        return hashlib.sha256(
            json.dumps(stable, sort_keys=True).encode()
        ).hexdigest()


@dataclass(frozen=True)
class RuleViolation:
    """A single rule evaluation failure."""

    rule_id: str
    severity: Literal["error", "warning", "info"]
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Aggregated output from running a rule set against a subject."""

    subject_id: str
    violations: list[RuleViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(v.severity == "error" for v in self.violations)

    @property
    def errors(self) -> list[RuleViolation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[RuleViolation]:
        return [v for v in self.violations if v.severity == "warning"]

    def add(self, violation: RuleViolation) -> None:
        self.violations.append(violation)
