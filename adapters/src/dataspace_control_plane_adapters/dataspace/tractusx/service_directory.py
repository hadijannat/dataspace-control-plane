"""Tractus-X Managed Identity Wallets and AAS Discovery endpoint directory.

Composition adapter — maps BPNs to service endpoints using Tractus-X conventions.
"""
from __future__ import annotations

from .config import TractuXSettings


class TractuXServiceDirectory:
    """Directory of Tractus-X service endpoints for a given BPN.

    Provides well-known endpoint lookups for Managed Identity Wallets and
    the EDR (Endpoint Data Reference) protocol without replicating protocol logic.
    """

    def __init__(self, cfg: TractuXSettings) -> None:
        self._cfg = cfg

    async def get_wallet_endpoint(self, bpn: str) -> str:
        """Return the Managed Identity Wallets endpoint for the given BPN.

        In production, this queries the Tractus-X central wallet registry.
        Currently returns a convention-based URL for the configured environment.

        Args:
            bpn: Business Partner Number (BPNL format).
        """
        # TODO: integrate with Tractus-X MIW registration API
        # Convention: wallet endpoints follow a known pattern per environment.
        env = self._cfg.environment
        return f"https://managed-identity-wallets.{env}.tractus-x.eu/api/wallets/{bpn}"

    async def get_edr_endpoint(self, bpn: str) -> str:
        """Return the EDR (Endpoint Data Reference) negotiation endpoint for the BPN.

        The EDR is used to negotiate short-lived bearer tokens for data-plane access.

        Args:
            bpn: Business Partner Number (BPNL format).
        """
        # EDR endpoint is typically derived from the connector protocol URL.
        # The actual EDR negotiation goes through the EDC management API.
        env = self._cfg.environment
        return f"https://edc.{env}.tractus-x.eu/{bpn}/api/v1/dsp"
