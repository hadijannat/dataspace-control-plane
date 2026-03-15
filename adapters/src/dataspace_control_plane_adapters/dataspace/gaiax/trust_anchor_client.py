"""Gaia-X Trust Anchor registry client.

Fetches the active trust anchor set for a given federation.
The Gaia-X Trust Framework allows federations to select subsets of trust anchors;
this adapter externalizes that selection via config.federation_id.
"""
from __future__ import annotations

import logging

from dataspace_control_plane_adapters._shared.http import AsyncAdapterClient
from .config import GaiaXSettings
from .errors import GaiaXTrustError

logger = logging.getLogger(__name__)


class GaiaXTrustAnchorClient:
    """Client for the Gaia-X Trust Anchor Registry."""

    def __init__(self, cfg: GaiaXSettings) -> None:
        self._cfg = cfg

    async def list_trust_anchors(self, federation_id: str) -> list[dict]:
        """Return the list of active trust anchors for the given federation.

        Each trust anchor dict contains: did, name, public_key_pem, active.

        Args:
            federation_id: Gaia-X federation identifier (e.g. "gaia-x-eu").
        """
        async with AsyncAdapterClient(
            str(self._cfg.trust_anchor_registry_url),
            timeout=self._cfg.request_timeout_s,
        ) as client:
            try:
                resp = await client.get(
                    f"/api/v1/trust-anchors?federation={federation_id}"
                )
                anchors = resp.json()
                if isinstance(anchors, list):
                    return anchors
                return anchors.get("trustAnchors", [])
            except Exception as exc:
                raise GaiaXTrustError(
                    f"Failed to list trust anchors for federation {federation_id!r}: {exc}"
                ) from exc

    async def is_trusted(self, issuer_did: str, federation_id: str) -> bool:
        """Return True if the issuer DID is in the active trust anchor set.

        Args:
            issuer_did: DID of the credential issuer to check.
            federation_id: Gaia-X federation identifier.
        """
        try:
            anchors = await self.list_trust_anchors(federation_id)
            trusted_dids = {a.get("did") for a in anchors if a.get("active", True)}
            return issuer_did in trusted_dids
        except GaiaXTrustError:
            return False
