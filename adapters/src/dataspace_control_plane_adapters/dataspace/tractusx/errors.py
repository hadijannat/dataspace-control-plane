"""Tractus-X adapter error types."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.errors import AdapterError, AdapterNotFoundError


class TractuXError(AdapterError):
    """Root for Tractus-X adapter errors."""


class BpnNotFoundError(AdapterNotFoundError):
    """No connector or DID found for the given BPN."""


class DiscoveryUnavailableError(TractuXError):
    """Tractus-X Discovery Service is unreachable."""
