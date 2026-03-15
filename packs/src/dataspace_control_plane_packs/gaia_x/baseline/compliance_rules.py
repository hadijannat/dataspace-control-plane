"""Gaia-X baseline compliance rules.

Defines the normative rules from the Gaia-X Trust Framework 22.10 that
apply to all participants regardless of which federation they belong to.

Implements :class:`RequirementProvider` as :class:`GaiaXComplianceValidator`.

No HTTP, DB, or Temporal code.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from ..._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult

_SOURCE_URI = (
    "https://docs.gaia-x.eu/policy-rules-committee/trust-framework/22.10/"
)
_SOURCE_VERSION = "22.10"
_EFFECTIVE_FROM = date(2022, 10, 1)

# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

PARTICIPANT_LEGAL_ADDRESS_REQUIRED = RuleDefinition(
    rule_id="gaiax:legal-address-required",
    title="Legal Address Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "required_field": "legal_address",
        "rationale": (
            "Every Gaia-X Legal Participant must declare a legal address "
            "per Trust Framework 22.10 §4."
        ),
    },
)

PARTICIPANT_LEGAL_REGISTRATION_REQUIRED = RuleDefinition(
    rule_id="gaiax:legal-registration-required",
    title="Legal Registration Number Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "required_field": "legal_registration_number",
        "rationale": (
            "Every Gaia-X Legal Participant must provide a legal registration "
            "number (EORI, VAT ID, LEI, or equivalent) per Trust Framework 22.10 §4."
        ),
    },
)

SELF_DESCRIPTION_REQUIRED = RuleDefinition(
    rule_id="gaiax:self-description-required",
    title="Self-Description Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "rationale": (
            "Every Gaia-X participant must publish a signed, verifiable "
            "Self-Description per Trust Framework 22.10 §5."
        ),
    },
)

COMPLIANCE_CREDENTIAL_REQUIRED = RuleDefinition(
    rule_id="gaiax:compliance-credential-recommended",
    title="Compliance Credential Recommended",
    severity="warning",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "rationale": (
            "A Gaia-X Compliance Credential issued by an accredited Conformity "
            "Assessment Body is recommended at baseline.  Some federations "
            "elevate this to a mandatory requirement."
        ),
    },
)

_ALL_RULES: tuple[RuleDefinition, ...] = (
    PARTICIPANT_LEGAL_ADDRESS_REQUIRED,
    PARTICIPANT_LEGAL_REGISTRATION_REQUIRED,
    SELF_DESCRIPTION_REQUIRED,
    COMPLIANCE_CREDENTIAL_REQUIRED,
)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class GaiaXComplianceValidator:
    """Validates subjects against the Gaia-X baseline compliance rule set.

    Implements :class:`RequirementProvider`.
    """

    RULES: tuple[RuleDefinition, ...] = _ALL_RULES

    # ------------------------------------------------------------------
    # RequirementProvider interface
    # ------------------------------------------------------------------

    def requirements(
        self,
        *,
        context: dict[str, Any],  # noqa: ARG002
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return all active Gaia-X baseline rules."""
        return [r for r in self.RULES if r.is_active(on)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate ``subject`` against the Gaia-X baseline rule set.

        Checks performed:
          - legal_address present (error)
          - legal_registration_number present (error)
          - self_description present (error)
          - compliance_credential present (warning)
        """
        subject_id = str(subject.get("id", "unknown"))
        result = ValidationResult(subject_id=subject_id)

        def _check(rule: RuleDefinition, field: str, label: str) -> None:
            if not rule.is_active(on):
                return
            value = subject.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                result.add(
                    RuleViolation(
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        message=(
                            f"Subject '{subject_id}' is missing required field "
                            f"'{field}' ({label}) per Gaia-X Trust Framework {_SOURCE_VERSION}."
                        ),
                        context={
                            "subject_id": subject_id,
                            "missing_field": field,
                            "source_uri": _SOURCE_URI,
                        },
                    )
                )

        _check(PARTICIPANT_LEGAL_ADDRESS_REQUIRED, "legal_address", "Legal Address")
        _check(PARTICIPANT_LEGAL_REGISTRATION_REQUIRED, "legal_registration_number", "Legal Registration Number")
        _check(SELF_DESCRIPTION_REQUIRED, "self_description", "Self-Description")
        _check(COMPLIANCE_CREDENTIAL_REQUIRED, "compliance_credential", "Compliance Credential")

        return result
