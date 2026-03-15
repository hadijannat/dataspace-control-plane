"""JWKS fetcher and TTL-based cache for the Keycloak adapter.

The cache stores the raw JWK set keyed by ``kid`` (Key ID).  Each entry is
a JWK dict as returned by the Keycloak JWKS endpoint.

Thread safety: asyncio single-threaded — no locking required.

Refresh strategy
----------------
- On first access (cold start) the cache is populated synchronously within
  ``get_keys()``.
- On subsequent accesses the cached value is returned until ``ttl_s`` seconds
  have elapsed since the last successful refresh.
- If a verification fails due to an unknown ``kid``, the caller should call
  ``refresh()`` explicitly to pick up newly rotated keys, then retry once.

Usage::

    cache = JwksCache(settings)
    keys = await cache.get_keys()           # {kid: jwk_dict}
    await cache.refresh()                   # force refresh
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from dataspace_control_plane_adapters.infrastructure.keycloak.config import KeycloakSettings
from dataspace_control_plane_adapters.infrastructure.keycloak.errors import (
    KeycloakJwksRefreshError,
)

logger = logging.getLogger(__name__)


class JwksCache:
    """Fetches and caches JWKS from Keycloak.

    Keyed by ``kid`` (Key ID string) for O(1) lookup during token verification.

    Parameters
    ----------
    settings:
        ``KeycloakSettings`` instance.  Only ``jwks_uri`` and ``jwks_cache_ttl_s``
        are used.
    """

    def __init__(self, settings: KeycloakSettings) -> None:
        self._jwks_uri: str = settings.jwks_uri
        self._ttl_s: int = settings.jwks_cache_ttl_s
        self._keys: dict[str, dict] = {}
        self._fetched_at: float = 0.0  # epoch seconds

    async def get_keys(self) -> dict[str, dict]:
        """Return the cached JWK set, refreshing if stale.

        Returns
        -------
        dict mapping ``kid`` → JWK dict (raw, as returned by Keycloak).
        """
        if self._is_stale():
            await self.refresh()
        return dict(self._keys)

    async def refresh(self) -> None:
        """Force a fetch from the Keycloak JWKS endpoint.

        Raises
        ------
        KeycloakJwksRefreshError
            If the HTTP request fails or returns a non-200 status.
        """
        logger.debug("Refreshing JWKS from %s", self._jwks_uri)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self._jwks_uri)
        except httpx.RequestError as exc:
            raise KeycloakJwksRefreshError(
                f"Failed to reach JWKS endpoint {self._jwks_uri}: {exc}"
            ) from exc

        if resp.status_code != 200:
            raise KeycloakJwksRefreshError(
                f"JWKS endpoint returned HTTP {resp.status_code}: {resp.text[:256]}"
            )

        try:
            jwks: dict = resp.json()
            keys_list: list[dict] = jwks.get("keys", [])
        except Exception as exc:  # noqa: BLE001
            raise KeycloakJwksRefreshError(
                f"JWKS response is not valid JSON: {exc}"
            ) from exc

        # Index by kid for fast lookup.  Keys without a kid are stored under "".
        self._keys = {key.get("kid", ""): key for key in keys_list}
        self._fetched_at = time.monotonic()
        logger.info("JWKS refreshed: %d key(s) cached", len(self._keys))

    def _is_stale(self) -> bool:
        """Return True if the cache is empty or the TTL has elapsed."""
        if not self._keys:
            return True
        return (time.monotonic() - self._fetched_at) >= self._ttl_s
