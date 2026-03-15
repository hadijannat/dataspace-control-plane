"""Tractus-X Discovery Service client.

The Discovery Service maps BPN → list of connector endpoint URLs.
Composition adapter — delegates HTTP to AsyncAdapterClient.
"""
from __future__ import annotations

import logging
from typing import Any

from dataspace_control_plane_adapters._shared.http import AsyncAdapterClient
from .config import TractuXSettings
from .errors import BpnNotFoundError, DiscoveryUnavailableError

logger = logging.getLogger(__name__)


class TractusXDiscoveryClient:
    """Client for the Tractus-X Discovery Service.

    Used to look up connector EDC protocol endpoints by BPN.
    Does not own negotiation or protocol logic — that belongs in edc/ and dsp/.
    """

    def __init__(self, cfg: TractuXSettings) -> None:
        self._cfg = cfg

    async def lookup_connector_endpoints(self, bpn: str) -> list[str]:
        """Return the list of EDC protocol URLs for the given BPN.

        POSTs a BPN list to the Discovery Service and returns the matching
        connector endpoint URLs.

        Args:
            bpn: Business Partner Number (BPNL format) to look up.

        Returns:
            List of connector protocol endpoint URLs. Empty list if not found.

        Raises:
            DiscoveryUnavailableError: If the Discovery Service is unreachable.
        """
        async with AsyncAdapterClient(
            str(self._cfg.dataspace_discovery_url),
            timeout=self._cfg.request_timeout_s,
        ) as client:
            try:
                resp = await client.post(
                    "/api/v1.0/administration/connectors/discovery",
                    json=[bpn],
                )
                results: list[dict[str, Any]] = resp.json()
                endpoints: list[str] = []
                for entry in results:
                    if entry.get("businessPartnerNumber") == bpn:
                        urls = entry.get("connectorEndpoint", [])
                        if isinstance(urls, list):
                            endpoints.extend(urls)
                        elif isinstance(urls, str):
                            endpoints.append(urls)
                return endpoints
            except Exception as exc:
                raise DiscoveryUnavailableError(
                    f"Tractus-X Discovery Service unreachable: {exc}"
                ) from exc

    async def register_connector(self, bpn: str, connector_url: str) -> None:
        """Register a connector URL for the given BPN in the Discovery Service.

        Args:
            bpn: Business Partner Number (BPNL format).
            connector_url: The EDC connector protocol endpoint URL to register.
        """
        async with AsyncAdapterClient(
            str(self._cfg.dataspace_discovery_url),
            timeout=self._cfg.request_timeout_s,
        ) as client:
            await client.post(
                "/api/v1.0/administration/connectors",
                json={
                    "businessPartnerNumber": bpn,
                    "connectorEndpoint": connector_url,
                },
            )
            logger.info("Registered connector BPN=%s url=%s", bpn, connector_url)
