from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from dataspace_control_plane_core.domains._shared.time import utc_now
from dataspace_control_plane_core.canonical_models.identity import DidUri, CredentialEnvelope
from .enums import CredentialLifecycle, VerificationResult
from .value_objects import KeyRef, VerificationMethodRecord, TrustAnchor


@dataclass
class TrustParticipant(AggregateRoot):
    """Represents a participant's DID-based identity in the trust fabric."""
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId("__unset__"))
    did: DidUri | None = None
    verification_methods: list[VerificationMethodRecord] = field(default_factory=list)
    credentials: list[CredentialEnvelope] = field(default_factory=list)
    trust_anchors: list[TrustAnchor] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)

    def add_credential(self, envelope: CredentialEnvelope) -> None:
        self.credentials.append(envelope)

    def get_active_credentials(self, now: datetime | None = None) -> list[CredentialEnvelope]:
        effective_now = now or utc_now()
        return [c for c in self.credentials if c.expires_at is None or c.expires_at > effective_now]

    def revoke_credential(self, credential_id: str) -> None:
        self.credentials = [credential for credential in self.credentials if credential.id != credential_id]


@dataclass(frozen=True)
class DidDocumentRecord:
    did: DidUri
    verification_methods: tuple[VerificationMethodRecord, ...] = ()
    service_endpoints: tuple[str, ...] = ()
    resolved_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class CredentialRecord:
    credential_id: str
    issuer_did: DidUri
    subject_did: DidUri
    validity_starts_at: datetime
    validity_ends_at: datetime | None
    format: str
    status_reference: str | None = None


@dataclass(frozen=True)
class PresentationRequest:
    request_id: str
    verifier_did: DidUri | None
    challenge: str
    domain: str | None = None


@dataclass
class PresentationVerification(AggregateRoot):
    """Records the outcome of a verifiable presentation verification."""
    presenter_did: DidUri | None = None
    result: VerificationResult = VerificationResult.UNKNOWN
    credential_count: int = 0
    verified_at: datetime = field(default_factory=utc_now)
    failure_reason: str | None = None


@dataclass
class RevocationRecord(AggregateRoot):
    """Immutable record of a credential revocation."""
    credential_id: str = ""
    issuer_did: DidUri | None = None
    subject_did: DidUri | None = None
    revoked_at: datetime = field(default_factory=utc_now)
    reason: str | None = None
    lifecycle: CredentialLifecycle = CredentialLifecycle.REVOKED
