"""Registry payload builders for ESPR DPP.

Products must be registered in the Commission registry once it becomes
operational. The registry assigns a globally unique DPP reference that
links the product identifier to the digital passport.

Reference: Regulation (EU) 2024/1781 (ESPR)
Deadline note: Commission registry must be operational by 2026-07-19.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from ..._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult

_SOURCE_URI = "https://eur-lex.europa.eu/legal-content/EN-DE/TXT/?from=EN&uri=CELEX:32024R1781"
_SOURCE_VERSION = "2024/1781"
_EFFECTIVE_FROM = date(2024, 7, 19)


@dataclass
class RegistryEntry:
    """A DPP registry entry linking a product to its passport and data carrier.

    Attributes:
        product_id: Manufacturer product identifier (ISO/IEC 15459 format).
        dpp_id: Unique Digital Product Passport identifier.
        carrier_type: Type of physical data carrier on the product.
        registry_url: URL of the registry where the entry is stored.
        registered_at: ISO 8601 datetime string of registration.
    """

    product_id: str
    dpp_id: str
    carrier_type: str
    registry_url: str
    registered_at: str


def build_registry_payload(
    product_id: str,
    dpp_id: str,
    carrier_type: str,
) -> dict[str, Any]:
    """Build a canonical registry payload dict for submission to the Commission registry.

    Args:
        product_id: ISO/IEC 15459-compliant product identifier.
        dpp_id: Unique DPP identifier.
        carrier_type: Type of physical data carrier (qr_code, rfid, etc.).

    Returns:
        A plain dict suitable for registry API submission.
    """
    return {
        "product_id": product_id,
        "dpp_id": dpp_id,
        "carrier_type": carrier_type,
        "regulation_version": "2024/1781",
        "registry_schema_version": "1.0",
    }


REGISTRY_REGISTRATION_REQUIRED = RuleDefinition(
    rule_id="espr:registry-registration-required",
    title="Registry Registration Required",
    severity="error",
    machine_checkable=False,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "Product DPP must be registered in the Commission registry. "
            "Commission registry must be operational by 2026-07-19."
        ),
        "registry_operational_by": "2026-07-19",
    },
)

_ALL_REGISTRY_RULES: list[RuleDefinition] = [REGISTRY_REGISTRATION_REQUIRED]


class RegistryValidator:
    """Validates registry registration requirements."""

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return active registry rules applicable on ``on``."""
        return [r for r in _ALL_REGISTRY_RULES if r.is_active(on)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate ``subject`` registry registration.

        ``subject`` should contain ``registry_ref`` or ``registry_registered`` fields.
        """
        product_id = subject.get("product_id", "unknown")
        result = ValidationResult(subject_id=str(product_id))

        registry_ref = subject.get("registry_ref") or subject.get("registry_registered", False)
        if not registry_ref:
            result.add(
                RuleViolation(
                    rule_id=REGISTRY_REGISTRATION_REQUIRED.rule_id,
                    severity=REGISTRY_REGISTRATION_REQUIRED.severity,
                    message=(
                        f"Product {product_id!r} is not registered in the Commission registry. "
                        "Registration required once the registry is operational (by 2026-07-19)."
                    ),
                    context={"product_id": product_id},
                )
            )

        return result
