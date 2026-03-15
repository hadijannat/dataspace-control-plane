"""Gaia-X Self-Description model and validators.

Defines the required and optional fields for each Gaia-X Self-Description
type and provides a stateless validator that returns a :class:`ValidationResult`.

Normative reference: Gaia-X Trust Framework 22.10, §5.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..._shared.rule_model import RuleViolation, ValidationResult

_SOURCE_URI = (
    "https://docs.gaia-x.eu/policy-rules-committee/trust-framework/22.10/"
)

# Rule ID used for self-description field violations
_RULE_SD_REQUIRED = "gaiax:self-description-required"


@dataclass(frozen=True)
class SelfDescriptionSchema:
    """Schema descriptor for a Gaia-X Self-Description type.

    Attributes:
        subject_type:    Canonical type key (e.g. ``"participant"``).
        required_fields: Canonical field names that must be present.
        optional_fields: Canonical field names that are optional.
    """

    subject_type: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = field(default_factory=tuple)

    def __init__(
        self,
        subject_type: str,
        required_fields: list[str],
        optional_fields: list[str] | None = None,
    ) -> None:
        object.__setattr__(self, "subject_type", subject_type)
        object.__setattr__(self, "required_fields", tuple(required_fields))
        object.__setattr__(self, "optional_fields", tuple(optional_fields or []))


# ---------------------------------------------------------------------------
# Standard Gaia-X Self-Description schemas (Trust Framework 22.10)
# ---------------------------------------------------------------------------

PARTICIPANT_SD = SelfDescriptionSchema(
    subject_type="participant",
    required_fields=[
        "legal_name",
        "legal_registration_number",
        "headquarter_address",
        "legal_address",
    ],
    optional_fields=[
        "vat_id",
        "description",
        "parent_organization",
        "sub_organization",
    ],
)
"""Self-Description schema for a Gaia-X Legal Participant."""

SERVICE_SD = SelfDescriptionSchema(
    subject_type="service",
    required_fields=[
        "name",
        "provided_by",
        "terms_and_conditions",
        "policy",
    ],
    optional_fields=[
        "description",
        "aggregation_of",
        "depends_on",
        "data_protection_regime",
    ],
)
"""Self-Description schema for a Gaia-X Service Offering."""

RESOURCE_SD = SelfDescriptionSchema(
    subject_type="resource",
    required_fields=[
        "name",
        "produced_by",
        "exposed_through",
    ],
    optional_fields=[
        "description",
        "license",
        "policy",
        "contained_in",
    ],
)
"""Self-Description schema for a Gaia-X Data Resource."""


def validate_self_description(
    sd: dict[str, Any],
    schema: SelfDescriptionSchema,
) -> ValidationResult:
    """Validate ``sd`` against ``schema`` required fields.

    Args:
        sd:     Self-description dict to validate.
        schema: :class:`SelfDescriptionSchema` defining required fields.

    Returns:
        :class:`ValidationResult` with ``subject_id`` derived from
        ``sd.get("id", "unknown")``.
    """
    subject_id = str(sd.get("id", "unknown"))
    result = ValidationResult(subject_id=subject_id)

    for field_name in schema.required_fields:
        value = sd.get(field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            result.add(
                RuleViolation(
                    rule_id=_RULE_SD_REQUIRED,
                    severity="error",
                    message=(
                        f"Self-Description for subject type '{schema.subject_type}' "
                        f"is missing required field '{field_name}'."
                    ),
                    context={
                        "subject_id": subject_id,
                        "subject_type": schema.subject_type,
                        "missing_field": field_name,
                        "source_uri": _SOURCE_URI,
                    },
                )
            )

    return result
