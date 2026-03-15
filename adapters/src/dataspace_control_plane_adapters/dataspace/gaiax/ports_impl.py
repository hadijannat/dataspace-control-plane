"""Gaia-X adapter port implementations.

Implements core/domains/machine_trust/ports.py TrustAnchorResolverPort.
"""
from __future__ import annotations

import logging

from dataspace_control_plane_core.canonical_models.identity import DidUri
from dataspace_control_plane_core.domains.machine_trust.model.value_objects import (
    TrustAnchor,
)

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

    async def list_active(self, trust_scope: str) -> list[TrustAnchor]:
        """Return active trust anchors for the given trust scope.

        trust_scope identifies the Gaia-X trust domain (e.g. "gaia-x").
        The federation_id used for registry lookup is always the one from
        GaiaXSettings.federation_id — trust_scope is not used as a direct
        federation identifier to prevent callers from enumerating arbitrary
        federation endpoints.

        Args:
            trust_scope: Trust scope identifier from core/machine_trust/.
        """

        # federation_id is always taken from configuration.  The trust_scope
        # argument maps conceptually to the gaia-x trust domain but must never
        # be used as a direct federation identifier — that would allow callers
        # to enumerate arbitrary federation endpoints not sanctioned by the
        # operator.
        federation_id = self._cfg.federation_id
        anchors = await self._client.list_trust_anchors(federation_id)
        canonical_anchors: list[TrustAnchor] = []
        for anchor in anchors:
            if not anchor.get("active", True):
                continue
            did = str(anchor.get("did") or "").strip()
            if not did:
                logger.debug(
                    "Skipping Gaia-X trust anchor without DID for federation=%s: %s",
                    federation_id,
                    anchor,
                )
                continue
            canonical_anchors.append(
                TrustAnchor(
                    name=str(anchor.get("name") or did),
                    did=DidUri(uri=did),
                    trust_scope=trust_scope or "gaia-x",
                    is_active=True,
                )
            )
        return canonical_anchors
