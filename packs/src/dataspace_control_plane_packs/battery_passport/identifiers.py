"""Battery unique identifier rules under EU Battery Regulation.

Each battery subject to the passport requirement must carry a unique identifier
accessible via QR code or direct identifier scan, and the identifier must be
linked to the battery passport.

Reference: Regulation (EU) 2023/1542
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from .._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult

_SOURCE_URI = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L:2023:191:FULL"
_SOURCE_VERSION = "2023/1542"
_EFFECTIVE_FROM = date(2023, 8, 17)
_PASSPORT_EFFECTIVE_FROM = date(2027, 2, 18)

# Placeholder — battery identifier format to be confirmed against implementing acts.
# Format: alphanumeric string, 8–40 chars.
_BATTERY_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-_]{8,40}$")

BATTERY_ID_REQUIRED = RuleDefinition(
    rule_id="battery:unique-id-required",
    title="Unique Battery Identifier Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "Each battery subject to the passport requirement must carry a "
            "globally unique identifier."
        ),
    },
)

QR_ACCESS_REQUIRED = RuleDefinition(
    rule_id="battery:qr-access-required",
    title="QR/Identifier-Based DPP Access Required",
    severity="error",
    machine_checkable=False,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_PASSPORT_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "The battery passport must be accessible by scanning the QR code or "
            "entering the unique identifier."
        ),
    },
)

UNIQUE_ID_LINKED_TO_PASSPORT = RuleDefinition(
    rule_id="battery:unique-id-linked-to-passport",
    title="Unique Identifier Must Link to Battery Passport",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_PASSPORT_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "The unique battery identifier must be directly linked to the battery passport "
            "record, enabling retrieval of the full passport from the identifier."
        ),
    },
)

_ALL_IDENTIFIER_RULES: list[RuleDefinition] = [
    BATTERY_ID_REQUIRED,
    QR_ACCESS_REQUIRED,
    UNIQUE_ID_LINKED_TO_PASSPORT,
]


class BatteryIdentifierValidator:
    """Validates battery identifier format and passport linkage requirements."""

    def validate_battery_id(self, value: str) -> bool:
        """Return True if ``value`` matches the battery identifier format.

        Note: The precise format is subject to implementing acts under
        Regulation (EU) 2023/1542.
        """
        return bool(_BATTERY_ID_PATTERN.match(value))

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return active identifier rules applicable on ``on``."""
        return [r for r in _ALL_IDENTIFIER_RULES if r.is_active(on)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate battery identifier fields in ``subject``.

        ``subject`` should contain:
          - ``battery_id``: str
          - ``passport_linked``: bool (optional) — whether id links to passport
        """
        battery_id = subject.get("battery_id", "")
        result = ValidationResult(subject_id=str(battery_id) or "unknown")

        if not self.validate_battery_id(str(battery_id)):
            result.add(
                RuleViolation(
                    rule_id=BATTERY_ID_REQUIRED.rule_id,
                    severity=BATTERY_ID_REQUIRED.severity,
                    message=(
                        f"Battery identifier {battery_id!r} does not match the "
                        "required format (8-40 alphanumeric/dash/underscore characters)."
                    ),
                    context={"battery_id": battery_id},
                )
            )

        if not subject.get("passport_linked", False):
            result.add(
                RuleViolation(
                    rule_id=UNIQUE_ID_LINKED_TO_PASSPORT.rule_id,
                    severity=UNIQUE_ID_LINKED_TO_PASSPORT.severity,
                    message=(
                        f"Battery {battery_id!r} unique identifier is not linked to the passport."
                    ),
                    context={"battery_id": battery_id},
                )
            )

        return result
