"""Data carrier requirements for ESPR DPP.

Products subject to ESPR must carry a machine-readable data carrier
(e.g. QR code, RFID, NFC) that links to the Digital Product Passport.

Reference: Regulation (EU) 2024/1781 (ESPR)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from ..._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult

_SOURCE_URI = "https://eur-lex.europa.eu/legal-content/EN-DE/TXT/?from=EN&uri=CELEX:32024R1781"
_SOURCE_VERSION = "2024/1781"
_EFFECTIVE_FROM = date(2024, 7, 19)

DATA_CARRIER_TYPES = ["qr_code", "rfid", "data_matrix", "nfc"]


@dataclass
class DataCarrierRequirement:
    """Represents a data carrier attached to or accompanying a product.

    Attributes:
        carrier_type: One of the allowed carrier types (qr_code, rfid, data_matrix, nfc).
        link_to_dpp: Whether the carrier contains a direct link to the DPP.
        machine_readable: Whether the carrier is machine-readable.
    """

    carrier_type: str
    link_to_dpp: bool
    machine_readable: bool


DATA_CARRIER_REQUIRED = RuleDefinition(
    rule_id="espr:data-carrier-required",
    title="Data Carrier Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "allowed_types": DATA_CARRIER_TYPES,
        "description": (
            "Product must carry a machine-readable data carrier "
            "(QR code, RFID, NFC, or data matrix) enabling access to the DPP."
        ),
    },
)

DATA_CARRIER_DPP_LINK_REQUIRED = RuleDefinition(
    rule_id="espr:data-carrier-dpp-link-required",
    title="Data Carrier Must Link to DPP",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "The data carrier on the product must contain or encode a direct "
            "link to the Digital Product Passport."
        ),
    },
)

_ALL_DATA_CARRIER_RULES: list[RuleDefinition] = [
    DATA_CARRIER_REQUIRED,
    DATA_CARRIER_DPP_LINK_REQUIRED,
]


class DataCarrierValidator:
    """Validates data carrier presence and DPP link requirements."""

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return active data carrier rules applicable on ``on``."""
        return [r for r in _ALL_DATA_CARRIER_RULES if r.is_active(on)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate ``subject`` data carrier fields.

        ``subject`` should contain:
          - ``carrier_type``: str — one of the allowed carrier types
          - ``carrier_link_to_dpp``: bool
        """
        product_id = subject.get("product_id", "unknown")
        result = ValidationResult(subject_id=str(product_id))

        carrier_type = subject.get("carrier_type")
        if not carrier_type or carrier_type not in DATA_CARRIER_TYPES:
            result.add(
                RuleViolation(
                    rule_id=DATA_CARRIER_REQUIRED.rule_id,
                    severity=DATA_CARRIER_REQUIRED.severity,
                    message=(
                        f"Product {product_id!r} has no valid data carrier. "
                        f"Allowed types: {DATA_CARRIER_TYPES}"
                    ),
                    context={
                        "product_id": product_id,
                        "carrier_type": carrier_type,
                        "allowed_types": DATA_CARRIER_TYPES,
                    },
                )
            )

        carrier_link = subject.get("carrier_link_to_dpp", False)
        if not carrier_link:
            result.add(
                RuleViolation(
                    rule_id=DATA_CARRIER_DPP_LINK_REQUIRED.rule_id,
                    severity=DATA_CARRIER_DPP_LINK_REQUIRED.severity,
                    message=(
                        f"Product {product_id!r} data carrier does not link to the DPP."
                    ),
                    context={"product_id": product_id, "carrier_link_to_dpp": carrier_link},
                )
            )

        return result
