from __future__ import annotations
from typing import Protocol
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId
from dataspace_control_plane_core.canonical_models.identity import DidUri, PresentationEnvelope
from .model.aggregates import PresentationVerification, TrustParticipant


class TrustParticipantRepository(Protocol):
    async def get(self, tenant_id: TenantId, legal_entity_id: LegalEntityId) -> TrustParticipant: ...
    async def save(self, participant: TrustParticipant, expected_version: int) -> None: ...


class DidResolverPort(Protocol):
    async def resolve(self, did: DidUri) -> dict: ...  # Returns raw DID document

class DidRegistrarPort(Protocol):
    async def publish(self, did: DidUri, document: dict) -> None: ...

class CredentialIssuerPort(Protocol):
    async def issue(self, subject_did: DidUri, claims: dict, type_labels: list[str]) -> str: ...  # Returns raw VC JWT/JSON

class PresentationVerifierPort(Protocol):
    async def verify(self, presentation: PresentationEnvelope) -> "VerificationResult": ...  # noqa: F821

class SignerPort(Protocol):
    async def sign(self, payload: bytes, key_id: str) -> bytes: ...

class TrustAnchorResolverPort(Protocol):
    async def list_active(self, trust_scope: str) -> list["TrustAnchor"]: ...  # noqa: F821
