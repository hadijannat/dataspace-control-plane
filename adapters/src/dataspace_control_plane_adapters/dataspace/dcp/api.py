"""DCP adapter public API.

Import from here, not from individual modules. Internal module structure
may change; this surface is stable.

Exported symbols:
- DcpSettings              — adapter configuration
- DcpCredentialServiceClient — DCP Credential Service REST client
- DcpIssuerClient          — DCP Issuer Service REST client
- DcpVerifierClient        — DCP Verifier Service REST client
- DcpCredentialIssuer      — CredentialIssuerPort implementation
- DcpPresentationVerifier  — PresentationVerifierPort implementation
- DcpTrustAnchorResolver   — TrustAnchorResolverPort implementation
- SiTokenBuilder           — SI token construction helper
- decode_si_token          — SI token inspection helper
- DcpError, DcpCredentialError, DcpVerificationError, DcpTokenError — errors
"""
from __future__ import annotations

from .config import DcpSettings
from .credential_service_client import DcpCredentialServiceClient
from .errors import DcpCredentialError, DcpError, DcpTokenError, DcpVerificationError
from .issuer_client import DcpIssuerClient
from .ports_impl import DcpCredentialIssuer, DcpPresentationVerifier, DcpTrustAnchorResolver
from .si_token import SiTokenBuilder, decode_si_token
from .verifier_client import DcpVerifierClient

__all__ = [
    "DcpSettings",
    "DcpCredentialServiceClient",
    "DcpIssuerClient",
    "DcpVerifierClient",
    "DcpCredentialIssuer",
    "DcpPresentationVerifier",
    "DcpTrustAnchorResolver",
    "SiTokenBuilder",
    "decode_si_token",
    "DcpError",
    "DcpCredentialError",
    "DcpVerificationError",
    "DcpTokenError",
]
