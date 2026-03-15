"""Catena-X governance acceptance model.

Participants must accept the Data Exchange Governance (DEG) document and
register their connector in the Catena-X portal before they may participate
in the data space.

Reference: Catena-X Operating Model v4.0
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from .._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult

_SOURCE_URI = "https://catenax-ev.github.io/docs/operating-model/how-data-space-operations"
_SOURCE_VERSION = "4.0"
_EFFECTIVE_FROM = date(2024, 1, 1)


@dataclass
class GovernanceState:
    """Runtime governance state for a Catena-X participant.

    Attributes:
        bpnl: The legal entity's BPNL.
        deg_accepted: Whether the Data Exchange Governance has been accepted.
        deg_accepted_at: ISO 8601 datetime string of acceptance, or None.
        connector_registered: Whether the connector is registered in the portal.
    """

    bpnl: str
    deg_accepted: bool
    deg_accepted_at: str | None
    connector_registered: bool


GOVERNANCE_ACCEPTANCE_REQUIRED = RuleDefinition(
    rule_id="catenax:deg-acceptance-required",
    title="Data Exchange Governance Acceptance Required",
    severity="error",
    machine_checkable=False,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "Participant must have accepted the Catena-X Data Exchange Governance."
        )
    },
)

CONNECTOR_REGISTRATION_REQUIRED = RuleDefinition(
    rule_id="catenax:connector-registration-required",
    title="Connector Registration Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "Participant's connector must be registered in the Catena-X portal."
        )
    },
)

_ALL_GOVERNANCE_RULES: list[RuleDefinition] = [
    GOVERNANCE_ACCEPTANCE_REQUIRED,
    CONNECTOR_REGISTRATION_REQUIRED,
]


class CatenaxGovernanceValidator:
    """RequirementProvider enforcing Catena-X governance acceptance rules."""

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return all active governance rules applicable on ``on``."""
        return [r for r in _ALL_GOVERNANCE_RULES if r.is_active(on)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate ``subject`` against active governance rules.

        ``subject`` is expected to contain at minimum ``bpnl``,
        ``deg_accepted``, and ``connector_registered`` fields.
        """
        bpnl = subject.get("bpnl", "unknown")
        state = GovernanceState(
            bpnl=str(bpnl),
            deg_accepted=bool(subject.get("deg_accepted", False)),
            deg_accepted_at=subject.get("deg_accepted_at"),
            connector_registered=bool(subject.get("connector_registered", False)),
        )
        return validate_governance(state)


def validate_governance(state: GovernanceState) -> ValidationResult:
    """Run governance validation against a GovernanceState and return a ValidationResult."""
    result = ValidationResult(subject_id=state.bpnl)

    if not state.deg_accepted:
        result.add(
            RuleViolation(
                rule_id=GOVERNANCE_ACCEPTANCE_REQUIRED.rule_id,
                severity=GOVERNANCE_ACCEPTANCE_REQUIRED.severity,
                message=(
                    f"Participant {state.bpnl!r} has not accepted the "
                    "Catena-X Data Exchange Governance."
                ),
                context={"bpnl": state.bpnl, "deg_accepted": state.deg_accepted},
            )
        )

    if not state.connector_registered:
        result.add(
            RuleViolation(
                rule_id=CONNECTOR_REGISTRATION_REQUIRED.rule_id,
                severity=CONNECTOR_REGISTRATION_REQUIRED.severity,
                message=(
                    f"Participant {state.bpnl!r} does not have a connector "
                    "registered in the Catena-X portal."
                ),
                context={"bpnl": state.bpnl, "connector_registered": state.connector_registered},
            )
        )

    return result
