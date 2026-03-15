"""Canonical evidence bundle models for compliance and audit."""
from __future__ import annotations
from datetime import datetime
from pydantic import field_validator

from .common import CanonicalBase
from .enums import RetentionClass, RedactionClass


class EvidenceDigest(CanonicalBase):
    """Cryptographic digest of an evidence artifact."""
    algorithm: str      # e.g. "sha256"
    hex_value: str

    @field_validator("hex_value")
    @classmethod
    def must_be_hex(cls, v: str) -> str:
        try:
            bytes.fromhex(v)
        except ValueError:
            raise ValueError(f"EvidenceDigest.hex_value must be valid hex: {v!r}")
        return v.lower()


class SignatureEnvelope(CanonicalBase):
    """Reference to a detached signature (stored in KMS/Vault)."""
    signer_did: str
    signature_id: str       # Vault/KMS reference
    signed_at: datetime
    algorithm: str          # e.g. "EdDSA", "ES256"


class Attestation(CanonicalBase):
    """A signed assertion about a subject."""
    attester_did: str
    subject_id: str
    claim_type: str
    claim_value: str
    attested_at: datetime
    signature: SignatureEnvelope | None = None


class EvidenceItem(CanonicalBase):
    """A single evidence artifact within a bundle."""
    item_id: str
    artifact_type: str      # e.g. "workflow_history", "credential_presentation", "assessment_result"
    storage_uri: str
    digest: EvidenceDigest | None = None
    collected_at: datetime
    retention_class: RetentionClass = RetentionClass.SEVEN_YEARS
    redaction_class: RedactionClass = RedactionClass.NONE


class EvidenceBundle(CanonicalBase):
    """Grouped collection of evidence items for an assessment or agreement."""
    bundle_id: str
    tenant_id: str
    legal_entity_id: str | None = None
    subject_type: str       # e.g. "compliance_assessment", "agreement", "onboarding"
    subject_id: str
    items: list[EvidenceItem] = []
    sealed_at: datetime | None = None
    signature: SignatureEnvelope | None = None
