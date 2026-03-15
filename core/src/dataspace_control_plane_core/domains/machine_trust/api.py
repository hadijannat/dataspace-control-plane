"""Public API surface for machine_trust domain."""
from .services import MachineTrustService
from .ports import (
    TrustParticipantRepository, DidResolverPort, DidRegistrarPort,
    CredentialIssuerPort, PresentationVerifierPort, SignerPort, TrustAnchorResolverPort,
)
from .commands import RegisterDidCommand, AddCredentialCommand, RevokeCredentialCommand
from .events import DidRegistered, CredentialAdded, CredentialRevoked
from .model.aggregates import (
    CredentialRecord,
    DidDocumentRecord,
    PresentationRequest,
    PresentationVerification,
    RevocationRecord,
    TrustParticipant,
)
from .model.value_objects import KeyBindingRef, KeyRef, VerificationMethodRecord, TrustAnchor
from .model.enums import CredentialLifecycle, TrustScope, VerificationResult
from .errors import TrustParticipantNotFoundError, InvalidDidError, CredentialVerificationFailedError

__all__ = [
    "MachineTrustService",
    "TrustParticipantRepository", "DidResolverPort", "DidRegistrarPort",
    "CredentialIssuerPort", "PresentationVerifierPort", "SignerPort",
    "TrustParticipant", "DidDocumentRecord", "CredentialRecord",
    "PresentationRequest", "PresentationVerification", "RevocationRecord",
    "KeyRef", "KeyBindingRef", "VerificationMethodRecord", "TrustAnchor",
    "CredentialLifecycle", "TrustScope", "VerificationResult",
    "RegisterDidCommand", "AddCredentialCommand", "RevokeCredentialCommand",
    "DidRegistered", "CredentialAdded", "CredentialRevoked",
    "TrustParticipantNotFoundError", "InvalidDidError",
]
