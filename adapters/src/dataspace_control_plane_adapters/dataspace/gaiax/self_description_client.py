"""Gaia-X Self-Description (SD) client.

Fetches and publishes Gaia-X Self-Descriptions (JSON-LD linked-data documents).
Normalizes SD vocabulary into canonical dicts; does not introduce global core types.
"""
from __future__ import annotations

import logging

from dataspace_control_plane_adapters._shared.http import AsyncAdapterClient
from .config import GaiaXSettings
from .errors import GaiaXSelfDescriptionError

logger = logging.getLogger(__name__)


class GaiaXSelfDescriptionClient:
    """Client for fetching and publishing Gaia-X Self-Descriptions."""

    def __init__(self, cfg: GaiaXSettings) -> None:
        self._cfg = cfg

    async def fetch_sd(self, participant_did: str) -> dict:
        """Fetch the Self-Description for a participant DID.

        Resolves the DID to its SD document using the Gaia-X SD resolver.
        Returns the raw JSON-LD document.

        Args:
            participant_did: DID of the Gaia-X participant (e.g. did:web:...).
        """
        async with AsyncAdapterClient(
            str(self._cfg.compliance_service_url),
            timeout=self._cfg.request_timeout_s,
        ) as client:
            try:
                resp = await client.get(
                    f"/api/v1/self-descriptions?id={participant_did}"
                )
                data = resp.json()
                if isinstance(data, list) and data:
                    return data[0]
                return data
            except Exception as exc:
                raise GaiaXSelfDescriptionError(
                    f"Failed to fetch SD for DID {participant_did!r}: {exc}"
                ) from exc

    async def publish_sd(self, sd: dict) -> str:
        """Publish a Gaia-X Self-Description to the compliance catalogue.

        Args:
            sd: The Self-Description JSON-LD document.

        Returns:
            URI of the published Self-Description.
        """
        async with AsyncAdapterClient(
            str(self._cfg.compliance_service_url),
            timeout=self._cfg.request_timeout_s,
        ) as client:
            try:
                resp = await client.post("/api/v1/self-descriptions", json=sd)
                result = resp.json()
                return result.get("id") or result.get("uri") or ""
            except Exception as exc:
                raise GaiaXSelfDescriptionError(
                    f"Failed to publish SD: {exc}"
                ) from exc
