from enum import Enum

class CredentialLifecycle(str, Enum):
    DRAFT = "draft"
    REQUESTED = "requested"
    ISSUED = "issued"
    PRESENTED = "presented"
    VERIFIED = "verified"
    REVOKED = "revoked"
    EXPIRED = "expired"

class TrustScope(str, Enum):
    GAIA_X = "gaia-x"
    CATENA_X = "catena-x"
    CUSTOM = "custom"

class VerificationResult(str, Enum):
    VALID = "valid"
    INVALID_SIGNATURE = "invalid_signature"
    REVOKED = "revoked"
    EXPIRED = "expired"
    UNTRUSTED_ISSUER = "untrusted_issuer"
    UNKNOWN = "unknown"
