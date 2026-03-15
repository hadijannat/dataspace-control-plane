"""EDC Management API base client.

All EDC management API calls go through this module. Concrete resource
clients (catalog, negotiation, transfer, asset) delegate to this class.

Auth pattern: EDC ``web.http.management.auth.type=tokenbased`` sends the
API key as an ``X-Api-Key`` header on every request.
"""
from __future__ import annotations

import logging
from typing import Any

from ..._shared.auth import StaticTokenProvider
from ..._shared.errors import AdapterNotFoundError
from ..._shared.http import AsyncAdapterClient
from .config import EdcSettings

logger = logging.getLogger(__name__)

_EDC_JSONLD_CONTEXT = "https://w3id.org/edc/v0.0.1/ns/"


class EdcManagementClient:
    """Base wrapper around the EDC Management API.

    Provides GET / POST / PUT / DELETE helpers that automatically:
    - Inject the ``X-Api-Key`` header on every request.
    - Return parsed JSON dicts (never raw bytes).
    - Translate EDC's quirky 404-on-empty-list to an empty list.
    - Log request/response at DEBUG level.

    Usage::
        async with EdcManagementClient(settings) as client:
            assets = await client.list_paginated("/v2/assets")
    """

    def __init__(self, settings: EdcSettings) -> None:
        self._settings = settings
        api_key = settings.api_key.get_secret_value()
        self._http = AsyncAdapterClient(
            base_url=str(settings.management_url),
            token_provider=StaticTokenProvider(api_key),
            timeout=settings.request_timeout_s,
            # EDC tokenbased auth uses X-Api-Key; we also pass it through the
            # static extra headers so it is present even if the token_provider
            # path is short-circuited by a subclass override.
            headers={"X-Api-Key": api_key},
        )

    async def __aenter__(self) -> "EdcManagementClient":
        await self._http.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._http.__aexit__(*args)

    # ------------------------------------------------------------------
    # Public HTTP helpers
    # ------------------------------------------------------------------

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """HTTP GET — returns parsed JSON dict."""
        resp = await self._http.get(path, **kwargs)
        return resp.json()

    async def post(self, path: str, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """HTTP POST with JSON body — returns parsed JSON dict."""
        resp = await self._http.post(path, json=body, **kwargs)
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    async def put(self, path: str, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """HTTP PUT with JSON body — returns parsed JSON dict."""
        resp = await self._http.put(path, json=body, **kwargs)
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    async def delete(self, path: str, **kwargs: Any) -> None:
        """HTTP DELETE — returns nothing on success."""
        await self._http.delete(path, **kwargs)

    async def list_paginated(
        self,
        path: str,
        page_size: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all items from an offset/limit paginated EDC list endpoint.

        EDC quirk: when no items exist the endpoint returns HTTP 404 with an
        empty body or an empty ``content`` array. This method translates that
        to an empty list rather than raising ``AdapterNotFoundError``.
        """
        size = page_size or self._settings.page_size
        results: list[dict[str, Any]] = []
        offset = 0

        while True:
            body = {
                "@context": {"@vocab": _EDC_JSONLD_CONTEXT},
                "offset": offset,
                "limit": size,
            }
            try:
                resp = await self._http.post(
                    f"{path}/request",
                    json=body,
                )
            except AdapterNotFoundError:
                # EDC returns 404 when the result set is empty.
                logger.debug("EDC returned 404 for list on %s — treating as empty", path)
                break

            if resp.status_code == 204 or not resp.content:
                break

            page: list[dict[str, Any]] = resp.json()
            if not isinstance(page, list):
                # Some EDC endpoints wrap the list in a "content" key.
                page = page.get("content", [])  # type: ignore[assignment]

            results.extend(page)

            if len(page) < size:
                break
            offset += size

        return results
