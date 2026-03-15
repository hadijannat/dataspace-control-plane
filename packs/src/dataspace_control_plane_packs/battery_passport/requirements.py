"""Battery passport requirement provider."""
from __future__ import annotations

from datetime import date
from typing import Any

from .._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult
from .identifiers import BatteryIdentifierValidator, BATTERY_ID_REQUIRED, QR_ACCESS_REQUIRED
from .linkage import validate_linkage


_RULES = [
    RuleDefinition(
        rule_id=BATTERY_ID_REQUIRED,
        title="Unique Battery Identifier Required",
        severity="error",
        machine_checkable=True,
        source_uri="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L:2023:191:FULL",
        source_version="2023/1542",
        effective_from=None,
        effective_to=None,
        scope={},
        payload={"field": "battery_id"},
    ),
    RuleDefinition(
        rule_id=QR_ACCESS_REQUIRED,
        title="QR/Identifier-Based DPP Access Required",
        severity="error",
        machine_checkable=False,
        source_uri="https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L:2023:191:FULL",
        source_version="2023/1542",
        effective_from=date(2027, 2, 18),
        effective_to=None,
        scope={},
        payload={"description": "QR code or unique identifier must link to the battery passport."},
    ),
]


class BatteryRequirementProvider:
    """Implements RequirementProvider for battery passport obligations."""

    def __init__(self) -> None:
        self._id_validator = BatteryIdentifierValidator()

    def requirements(
        self, *, context: dict[str, Any], on: date | None = None
    ) -> list[RuleDefinition]:
        check_date = on or date.today()
        return [r for r in _RULES if r.is_active(check_date)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        result = ValidationResult(subject_id=subject.get("battery_id", "unknown"))
        battery_id = subject.get("battery_id")
        if not battery_id:
            result.add(RuleViolation(
                rule_id=BATTERY_ID_REQUIRED,
                severity="error",
                message="battery_id is required",
            ))
        elif not self._id_validator.validate(battery_id):
            result.add(RuleViolation(
                rule_id=BATTERY_ID_REQUIRED,
                severity="error",
                message=f"battery_id {battery_id!r} does not match required format",
            ))
        # Check linkage rules for repurposed/remanufactured
        lifecycle_state = subject.get("lifecycle_state", "active")
        linkage_result = validate_linkage(subject, lifecycle_state)
        result.violations.extend(linkage_result.violations)
        return result
