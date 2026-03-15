"""Gaia-X adapter port implementations.

Implements core/domains/machine_trust/ports.py TrustAnchorResolverPort.
"""
from __future__ import annotations

import logging

from .config import GaiaXSettings
from .trust_anchor_client import GaiaXTrustAnchorClient

logger = logging.getLogger(__name__)


class GaiaXTrustAnchorAdapterPort:
    """Implements core/domains/machine_trust/ports.py TrustAnchorResolverPort.

    Maps trust_scope to federation_id for Gaia-X.
    Federation selection is configuration, not code: different federations
    are activated by changing GaiaXSettings.federation_id.
    """

    def __init__(self, cfg: GaiaXSettings) -> None:
        self._cfg = cfg
        self._client = GaiaXTrustAnchorClient(cfg)

    async def list_active(self, trust_scope: str) -> list[dict]:
        """Return active trust anchors for the given trust scope.

        trust_scope maps to federation_id in Gaia-X:
          - "gaia-x" → use configured federation_id
          - Any other scope string is treated as a direct federation_id override.

        Args:
            trust_scope: Trust scope identifier from core/machine_trust/.

        Returns:
            List of trust anchor dicts: {did, name, public_key_pem, active}.
        """
        federation_id = (
            self._cfg.federation_id
            if trust_scope in ("gaia-x", "gaiax", "")
            else trust_scope
        )
        anchors = await self._client.list_trust_anchors(federation_id)
        return [a for a in anchors if a.get("active", True)]
