"""Tractus-X composition adapter port implementations.

Composes lower-level adapters (edc/, dsp/, dcp/) to provide
Tractus-X ecosystem convenience lookups. No raw protocol code here.
"""
from __future__ import annotations

import logging

from .bpn_resolution import BpnResolver
from .config import TractuXSettings
from .discovery import TractusXDiscoveryClient

logger = logging.getLogger(__name__)


class TractuXConnectorLookup:
    """Ecosystem convenience lookup over BPN → connector identity.

    Wraps BpnResolver and TractusXDiscoveryClient to provide a single
    point of contact for connector discovery in the Tractus-X ecosystem.
    """

    def __init__(self, cfg: TractuXSettings) -> None:
        self._cfg = cfg
        self._resolver = BpnResolver(cfg)
        self._discovery = TractusXDiscoveryClient(cfg)

    async def find_connector(self, bpn: str) -> dict:
        """Resolve a BPN to its connector identity bundle.

        Args:
            bpn: Business Partner Number (BPNL format).

        Returns:
            Dict with keys: bpn, connector_url (str | None), did (str | None).
        """
        connector_url = await self._resolver.resolve_connector_url(bpn)
        did = await self._resolver.resolve_did(bpn)
        return {
            "bpn": bpn,
            "connector_url": connector_url,
            "did": did,
        }
