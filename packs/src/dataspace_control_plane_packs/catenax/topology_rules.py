"""Catena-X topology rules enforcing legal-entity-first participation.

Every participant must have a registered BPNL and at least one connector.
These are machine-checkable structural requirements from the Catena-X
Operating Model v4.0.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult
from .identifiers import BpnlSchemeProvider

_SOURCE_URI = "https://catenax-ev.github.io/docs/operating-model/how-data-space-operations"
_SOURCE_VERSION = "4.0"
_EFFECTIVE_FROM = date(2024, 1, 1)

BPNL_REQUIRED = RuleDefinition(
    rule_id="catenax:bpnl-required",
    title="BPNL Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={"description": "Every Catena-X participant must have a registered BPNL."},
)

CONNECTOR_REQUIRED = RuleDefinition(
    rule_id="catenax:connector-required",
    title="Connector Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={"description": "At least one connector must be registered per legal entity."},
)

ONE_CONNECTOR_PER_LEGAL_ENTITY = RuleDefinition(
    rule_id="catenax:one-connector-per-legal-entity",
    title="One Connector Per Legal Entity",
    severity="warning",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "It is recommended to register exactly one connector per legal entity "
            "to simplify governance and auditing."
        )
    },
)

_ALL_TOPOLOGY_RULES: list[RuleDefinition] = [
    BPNL_REQUIRED,
    CONNECTOR_REQUIRED,
    ONE_CONNECTOR_PER_LEGAL_ENTITY,
]

_bpnl_scheme = BpnlSchemeProvider()


class CatenaxTopologyValidator:
    """RequirementProvider enforcing Catena-X legal-entity-first topology rules."""

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return all active topology rules applicable on ``on``."""
        return [r for r in _ALL_TOPOLOGY_RULES if r.is_active(on)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate that ``subject`` has a valid BPNL and at least one connector_id."""
        subject_id = subject.get("bpnl") or subject.get("id") or "unknown"
        result = ValidationResult(subject_id=str(subject_id))

        bpnl = subject.get("bpnl", "")
        if not bpnl:
            result.add(
                RuleViolation(
                    rule_id=BPNL_REQUIRED.rule_id,
                    severity=BPNL_REQUIRED.severity,
                    message="Subject is missing a 'bpnl' field.",
                    context={"subject_keys": list(subject.keys())},
                )
            )
        elif not _bpnl_scheme.validate(bpnl):
            result.add(
                RuleViolation(
                    rule_id=BPNL_REQUIRED.rule_id,
                    severity=BPNL_REQUIRED.severity,
                    message=f"'bpnl' value {bpnl!r} does not match the BPNL pattern.",
                    context={"bpnl": bpnl},
                )
            )

        connector_ids = subject.get("connector_ids", [])
        if isinstance(connector_ids, str):
            connector_ids = [connector_ids]
        connector_id = subject.get("connector_id")
        if connector_id and connector_id not in connector_ids:
            connector_ids = list(connector_ids) + [connector_id]

        if not connector_ids:
            result.add(
                RuleViolation(
                    rule_id=CONNECTOR_REQUIRED.rule_id,
                    severity=CONNECTOR_REQUIRED.severity,
                    message="Subject must have at least one connector_id registered.",
                    context={"bpnl": bpnl},
                )
            )
        elif len(connector_ids) > 1:
            result.add(
                RuleViolation(
                    rule_id=ONE_CONNECTOR_PER_LEGAL_ENTITY.rule_id,
                    severity=ONE_CONNECTOR_PER_LEGAL_ENTITY.severity,
                    message=(
                        f"Subject has {len(connector_ids)} connectors registered; "
                        "it is recommended to use exactly one per legal entity."
                    ),
                    context={"connector_count": len(connector_ids), "bpnl": bpnl},
                )
            )

        return result
