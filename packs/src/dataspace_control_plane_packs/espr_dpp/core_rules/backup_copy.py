"""Backup copy requirement for ESPR DPP.

Manufacturers must maintain a backup copy of the DPP to ensure
continuity of access even if the primary storage becomes unavailable.

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


@dataclass
class BackupCopyEvidence:
    """Evidence record for a DPP backup copy.

    Attributes:
        backup_location_uri: URI of the backup storage location.
        backup_created_at: ISO 8601 datetime string when the backup was created.
        checksum_sha256: SHA-256 hex digest of the backed-up DPP payload.
    """

    backup_location_uri: str
    backup_created_at: str
    checksum_sha256: str


BACKUP_COPY_REQUIRED = RuleDefinition(
    rule_id="espr:backup-copy-required",
    title="Backup Copy Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=_EFFECTIVE_FROM,
    effective_to=None,
    scope={},
    payload={
        "description": (
            "A backup copy of the DPP must be maintained to ensure continued "
            "accessibility if the primary DPP storage becomes unavailable."
        ),
    },
)

_ALL_BACKUP_RULES: list[RuleDefinition] = [BACKUP_COPY_REQUIRED]


def validate_backup_evidence(evidence: dict[str, Any]) -> ValidationResult:
    """Validate backup evidence fields for completeness.

    Args:
        evidence: Dict that should contain ``backup_location_uri``,
            ``backup_created_at``, and ``checksum_sha256``.

    Returns:
        ValidationResult with violations for any missing required fields.
    """
    subject_id = evidence.get("product_id", evidence.get("dpp_id", "unknown"))
    result = ValidationResult(subject_id=str(subject_id))

    backup_location = evidence.get("backup_location_uri", "")
    backup_created = evidence.get("backup_created_at", "")
    checksum = evidence.get("checksum_sha256", "")

    if not backup_location or not backup_created or not checksum:
        missing = []
        if not backup_location:
            missing.append("backup_location_uri")
        if not backup_created:
            missing.append("backup_created_at")
        if not checksum:
            missing.append("checksum_sha256")
        result.add(
            RuleViolation(
                rule_id=BACKUP_COPY_REQUIRED.rule_id,
                severity=BACKUP_COPY_REQUIRED.severity,
                message=(
                    f"DPP backup evidence for {subject_id!r} is incomplete. "
                    f"Missing fields: {missing}"
                ),
                context={
                    "subject_id": subject_id,
                    "missing_fields": missing,
                },
            )
        )

    return result


class BackupCopyValidator:
    """Validates DPP backup copy requirements."""

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return active backup copy rules applicable on ``on``."""
        return [r for r in _ALL_BACKUP_RULES if r.is_active(on)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate backup copy fields in ``subject``."""
        return validate_backup_evidence(subject)
