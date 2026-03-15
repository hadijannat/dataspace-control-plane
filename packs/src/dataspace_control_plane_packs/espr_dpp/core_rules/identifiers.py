"""ISO/IEC 15459-compatible identifier rules for ESPR DPP.

The DPP unique identifier must be structured per ISO/IEC 15459 to ensure
global uniqueness and interoperability across product groups and member states.

Reference: Regulation (EU) 2024/1781 (ESPR)
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from ..._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult

_SOURCE_URI = "https://eur-lex.europa.eu/legal-content/EN-DE/TXT/?from=EN&uri=CELEX:32024R1781"
_SOURCE_VERSION = "2024/1781"
_EFFECTIVE_FROM = date(2024, 7, 19)

ISO15459_SCHEME = "iso-iec-15459"

# Placeholder pattern — must be verified against ISO/IEC 15459 specification.
# Format: <issuing-agency-code (2-8 uppercase alphanumeric)>.<unique-item-ref (6-30 uppercase alphanumeric)>
DPP_IDENTIFIER_PATTERN = re.compile(r"^[A-Z0-9]{2,8}\.[A-Z0-9]{6,30}$")

IDENTIFIER_REQUIRED = RuleDefinition(
    rule_id="espr:iso-15459-identifier-required",
    title="ISO/IEC 15459 Compatible Identifier Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "scheme": ISO15459_SCHEME,
        "pattern": DPP_IDENTIFIER_PATTERN.pattern,
        "description": (
            "DPP unique identifier must be structured per ISO/IEC 15459 "
            "to ensure global uniqueness across product groups and member states."
        ),
    },
)

_ALL_IDENTIFIER_RULES: list[RuleDefinition] = [IDENTIFIER_REQUIRED]


class EsprIdentifierValidator:
    """Validates that a product identifier is structured per ISO/IEC 15459."""

    def validate_identifier(self, value: str) -> bool:
        """Return True if ``value`` matches the ISO/IEC 15459-compatible DPP format."""
        return bool(DPP_IDENTIFIER_PATTERN.match(value))

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
        """Validate ``subject`` identifier field against ISO/IEC 15459 format.

        ``subject`` must contain a ``product_id`` field.
        """
        product_id = subject.get("product_id", "")
        result = ValidationResult(subject_id=str(product_id) or "unknown")

        if not self.validate_identifier(str(product_id)):
            result.add(
                RuleViolation(
                    rule_id=IDENTIFIER_REQUIRED.rule_id,
                    severity=IDENTIFIER_REQUIRED.severity,
                    message=(
                        f"Product identifier {product_id!r} does not conform to "
                        "ISO/IEC 15459 format. Expected pattern: "
                        f"{DPP_IDENTIFIER_PATTERN.pattern}"
                    ),
                    context={"product_id": product_id, "scheme": ISO15459_SCHEME},
                )
            )

        return result
