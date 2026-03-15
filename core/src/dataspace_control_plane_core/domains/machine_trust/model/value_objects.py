from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

from dataspace_control_plane_core.canonical_models.identity import DidUri


@dataclass(frozen=True)
class KeyRef:
    """Reference to a key in KMS/Vault. Never stores key material."""
    key_id: str          # Vault/KMS path or alias
    key_type: str        # e.g. "Ed25519", "P-256", "RSA"
    public_key_multibase: str | None = None  # Public key for verification only


@dataclass(frozen=True)
class VerificationMethodRecord:
    method_id: str       # Full DID#fragment URI
    method_type: str     # e.g. "Ed25519VerificationKey2020"
    controller: str
    key_ref: KeyRef | None = None


@dataclass(frozen=True)
class TrustAnchor:
    name: str
    did: DidUri
    trust_scope: str
    is_active: bool = True


KeyBindingRef = KeyRef
