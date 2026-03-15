"""
Canonical identity models: DID/VC/DCP primitives.
Normalized from W3C DID Core, VC 2.0, and DCP specs.
No raw Keycloak tokens, EDC management DTOs, or transport envelopes here.
"""
from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import field_validator

from .common import CanonicalBase
from .enums import CredentialFormat


class DidUri(CanonicalBase):
    """A W3C DID URI, e.g. did:web:example.com or did:key:z6Mk..."""
    uri: str

    @field_validator("uri")
    @classmethod
    def must_start_with_did(cls, v: str) -> str:
        if not v.startswith("did:"):
            raise ValueError(f"Invalid DID URI: {v!r}")
        return v

    def method(self) -> str:
        return self.uri.split(":")[1]

    def __str__(self) -> str:
        return self.uri


class VerificationMethodRef(CanonicalBase):
    """Reference to a DID verification method (key material location)."""
    did_uri: DidUri
    fragment: str  # e.g. "#key-1"

    def full_uri(self) -> str:
        return f"{self.did_uri.uri}{self.fragment}"


class ServiceEndpointRef(CanonicalBase):
    """Normalized reference to a DID service endpoint."""
    service_type: str  # e.g. "CredentialService", "LinkedDomains"
    endpoint_url: str


class DidDocumentRef(CanonicalBase):
    """Reference to a resolved DID document (not the full document)."""
    did: DidUri
    controller: DidUri | None = None
    verification_method_refs: list[VerificationMethodRef] = []
    service_endpoints: list[ServiceEndpointRef] = []
    resolved_at: datetime | None = None


class CredentialStatusRef(CanonicalBase):
    """Reference to a credential status list entry (StatusList2021 or equivalent)."""
    status_list_uri: str
    status_index: int
    status_type: str  # e.g. "StatusList2021Entry"


class TrustAnchorRef(CanonicalBase):
    """Reference to an accepted trust anchor (e.g. Gaia-X AISBL, Catena-X CA)."""
    name: str
    did: DidUri
    trust_scope: str  # e.g. "gaia-x", "catena-x", "custom"


class CredentialEnvelope(CanonicalBase):
    """
    Normalized VC envelope for storage and routing.
    Does not contain the raw credential bytes — only references and metadata.
    """
    id: str  # vc_id
    format: CredentialFormat
    issuer_did: DidUri
    subject_did: DidUri
    type_labels: list[str]
    issued_at: datetime
    expires_at: datetime | None = None
    status: CredentialStatusRef | None = None
    trust_anchor: TrustAnchorRef | None = None


class PresentationEnvelope(CanonicalBase):
    """Normalized VP envelope."""
    id: str
    holder_did: DidUri
    credentials: list[CredentialEnvelope]
    created_at: datetime
    challenge: str | None = None
    domain: str | None = None
