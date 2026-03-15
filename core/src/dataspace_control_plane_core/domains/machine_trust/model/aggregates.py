from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from dataspace_control_plane_core.canonical_models.identity import DidUri, CredentialEnvelope
from .enums import CredentialLifecycle, VerificationResult
from .value_objects import KeyRef, VerificationMethodRecord, TrustAnchor


@dataclass
class TrustParticipant(AggregateRoot):
    """Represents a participant's DID-based identity in the trust fabric."""
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId(""))
    did: DidUri | None = None
    verification_methods: list[VerificationMethodRecord] = field(default_factory=list)
    credentials: list[CredentialEnvelope] = field(default_factory=list)
    trust_anchors: list[TrustAnchor] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_credential(self, envelope: CredentialEnvelope) -> None:
        self.credentials.append(envelope)

    def get_active_credentials(self) -> list[CredentialEnvelope]:
        now = datetime.now(timezone.utc)
        return [c for c in self.credentials if c.expires_at is None or c.expires_at > now]


@dataclass
class PresentationVerification(AggregateRoot):
    """Records the outcome of a verifiable presentation verification."""
    presenter_did: DidUri | None = None
    result: VerificationResult = VerificationResult.UNKNOWN
    credential_count: int = 0
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    failure_reason: str | None = None


@dataclass
class RevocationRecord(AggregateRoot):
    """Immutable record of a credential revocation."""
    credential_id: str = ""
    issuer_did: DidUri | None = None
    subject_did: DidUri | None = None
    revoked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str | None = None
