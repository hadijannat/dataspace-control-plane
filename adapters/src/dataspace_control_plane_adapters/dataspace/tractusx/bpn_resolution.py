"""BPN → DID / connector URL resolution for Tractus-X.

Composes TractusXDiscoveryClient to provide BPN resolution without
reimplementing protocol logic.
"""
from __future__ import annotations

import logging

from .config import TractuXSettings
from .discovery import TractusXDiscoveryClient
from .errors import BpnNotFoundError

logger = logging.getLogger(__name__)


class BpnResolver:
    """Resolves BPN identifiers to DIDs and connector URLs.

    Composition adapter — wraps TractusXDiscoveryClient.
    No DSP negotiation code. No ODRL. No wallet semantics.
    """

    def __init__(self, cfg: TractuXSettings) -> None:
        self._cfg = cfg
        self._discovery = TractusXDiscoveryClient(cfg)

    async def resolve_connector_url(self, bpn: str) -> str | None:
        """Return the first connector EDC protocol URL for the given BPN, or None.

        Args:
            bpn: Business Partner Number (BPNL format).
        """
        endpoints = await self._discovery.lookup_connector_endpoints(bpn)
        return endpoints[0] if endpoints else None

    async def resolve_did(self, bpn: str) -> str | None:
        """Return the DID for the given BPN, or None if not available.

        In Tractus-X, DIDs are typically registered in the Managed Identity
        Wallets service. This method provides a best-effort lookup via the
        Discovery Service connector endpoint conventions.

        Args:
            bpn: Business Partner Number (BPNL format).
        """
        # TODO: integrate with Managed Identity Wallets DID resolver
        # For now, derive a did:web from the connector URL convention.
        connector_url = await self.resolve_connector_url(bpn)
        if connector_url is None:
            return None
        # Tractus-X convention: did:web derived from connector hostname
        from urllib.parse import urlparse
        parsed = urlparse(connector_url)
        host = parsed.netloc.replace(":", "%3A")
        return f"did:web:{host}"

    async def require_connector_url(self, bpn: str) -> str:
        """Return the connector URL for the given BPN, raising if not found.

        Raises:
            BpnNotFoundError: If no connector endpoint is registered for the BPN.
        """
        url = await self.resolve_connector_url(bpn)
        if url is None:
            raise BpnNotFoundError(f"No connector endpoint found for BPN {bpn!r}")
        return url
