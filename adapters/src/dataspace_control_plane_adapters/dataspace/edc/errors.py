"""EDC-specific error hierarchy.

These errors are raised by EDC adapter internals and translated at the
ports_impl.py boundary into core-compatible exceptions before propagating
upward into procedures/ or apps/.
"""
from __future__ import annotations

from ..._shared.errors import (
    AdapterError,
    AdapterNotFoundError,
    AdapterValidationError,
)


class EdcError(AdapterError):
    """Root for all EDC adapter errors."""


class EdcNegotiationError(EdcError):
    """Error during contract negotiation with EDC (state machine violation, etc.)."""


class EdcTransferError(EdcError):
    """Error during transfer process lifecycle with EDC."""


class EdcAssetNotFoundError(AdapterNotFoundError):
    """EDC asset does not exist (HTTP 404 on asset endpoint)."""


class EdcPolicyNotFoundError(AdapterNotFoundError):
    """EDC policy definition does not exist."""


class EdcWebhookParseError(AdapterValidationError):
    """Failed to parse or validate an incoming EDC webhook/callback payload."""
