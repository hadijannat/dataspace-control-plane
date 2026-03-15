"""DPP accessibility requirements under ESPR.

The DPP must be accessible via open standards, be machine-readable,
use interoperable formats, and be transferable through open networks.
No proprietary or closed-standard data exchange is permitted.

Reference: Regulation (EU) 2024/1781 (ESPR)
"""
from __future__ import annotations

from datetime import date
from typing import Any

from ..._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult

_SOURCE_URI = "https://eur-lex.europa.eu/legal-content/EN-DE/TXT/?from=EN&uri=CELEX:32024R1781"
_SOURCE_VERSION = "2024/1781"
_EFFECTIVE_FROM = date(2024, 7, 19)

OPEN_STANDARD_REQUIRED = RuleDefinition(
    rule_id="espr:open-standard-required",
    title="Open Standard Required",
    severity="error",
    machine_checkable=False,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "DPP data must use open, publicly available standards. "
            "Proprietary data formats are not permitted."
        ),
    },
)

MACHINE_READABLE_REQUIRED = RuleDefinition(
    rule_id="espr:machine-readable-required",
    title="Machine-Readable Structured Data Required",
    severity="error",
    machine_checkable=False,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "DPP data must be structured and machine-readable to enable "
            "automated processing and searchability."
        ),
    },
)

INTEROPERABLE_FORMAT_REQUIRED = RuleDefinition(
    rule_id="espr:interoperable-format-required",
    title="Interoperable Format Required",
    severity="error",
    machine_checkable=False,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "DPP data must use interoperable formats with no vendor lock-in. "
            "Consumers must be able to read the data without proprietary tools."
        ),
    },
)

OPEN_NETWORK_REQUIRED = RuleDefinition(
    rule_id="espr:open-network-required",
    title="Open Network Data Exchange Required",
    severity="error",
    machine_checkable=False,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "DPP data must be transferable through an open, interoperable "
            "data exchange network. Closed or proprietary networks are not permitted."
        ),
    },
)

_ALL_ACCESSIBILITY_RULES: list[RuleDefinition] = [
    OPEN_STANDARD_REQUIRED,
    MACHINE_READABLE_REQUIRED,
    INTEROPERABLE_FORMAT_REQUIRED,
    OPEN_NETWORK_REQUIRED,
]


class EsprAccessibilityValidator:
    """RequirementProvider enforcing ESPR DPP accessibility requirements."""

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return all active accessibility rules applicable on ``on``."""
        return [r for r in _ALL_ACCESSIBILITY_RULES if r.is_active(on)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate ``subject`` against active accessibility rules.

        Since all accessibility rules are non-machine-checkable, this method
        checks only for explicit declarations in ``subject``:
          - ``uses_open_standard``: bool
          - ``machine_readable``: bool
          - ``interoperable_format``: bool
          - ``open_network``: bool
        """
        product_id = subject.get("product_id", "unknown")
        result = ValidationResult(subject_id=str(product_id))

        if not subject.get("uses_open_standard", False):
            result.add(
                RuleViolation(
                    rule_id=OPEN_STANDARD_REQUIRED.rule_id,
                    severity=OPEN_STANDARD_REQUIRED.severity,
                    message=(
                        f"Product {product_id!r} DPP does not declare use of open standards."
                    ),
                    context={"product_id": product_id},
                )
            )

        if not subject.get("machine_readable", False):
            result.add(
                RuleViolation(
                    rule_id=MACHINE_READABLE_REQUIRED.rule_id,
                    severity=MACHINE_READABLE_REQUIRED.severity,
                    message=(
                        f"Product {product_id!r} DPP data is not declared as machine-readable."
                    ),
                    context={"product_id": product_id},
                )
            )

        if not subject.get("interoperable_format", False):
            result.add(
                RuleViolation(
                    rule_id=INTEROPERABLE_FORMAT_REQUIRED.rule_id,
                    severity=INTEROPERABLE_FORMAT_REQUIRED.severity,
                    message=(
                        f"Product {product_id!r} DPP does not declare an interoperable format."
                    ),
                    context={"product_id": product_id},
                )
            )

        if not subject.get("open_network", False):
            result.add(
                RuleViolation(
                    rule_id=OPEN_NETWORK_REQUIRED.rule_id,
                    severity=OPEN_NETWORK_REQUIRED.severity,
                    message=(
                        f"Product {product_id!r} DPP is not declared as exchanged over an "
                        "open, interoperable network."
                    ),
                    context={"product_id": product_id},
                )
            )

        return result
