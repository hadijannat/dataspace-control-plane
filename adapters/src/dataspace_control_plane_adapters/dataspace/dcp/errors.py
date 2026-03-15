"""DCP-specific error types.

All DCP errors subclass adapter-layer base types so they can be caught
uniformly at the ports_impl boundary without leaking DCP-specific types.
"""
from __future__ import annotations

from ..._shared.errors import AdapterAuthError, AdapterError


class DcpError(AdapterError):
    """Root for all DCP adapter errors."""


class DcpCredentialError(DcpError):
    """Credential issuance or retrieval failed at the DCP Credential Service."""


class DcpVerificationError(DcpError):
    """Presentation or credential verification failed at the DCP Verifier."""


class DcpTokenError(AdapterAuthError):
    """Self-Issued Identity token construction or validation failed."""
