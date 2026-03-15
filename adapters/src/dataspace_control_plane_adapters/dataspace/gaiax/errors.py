"""Gaia-X adapter error types."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.errors import AdapterAuthError, AdapterError


class GaiaXError(AdapterError):
    """Root for Gaia-X adapter errors."""


class GaiaXComplianceError(GaiaXError):
    """Compliance check failed or compliance service is unavailable."""


class GaiaXTrustError(AdapterAuthError):
    """Issuer DID is not in the active trust anchor set for the federation."""


class GaiaXSelfDescriptionError(GaiaXError):
    """Self-description fetch or publication failed."""
