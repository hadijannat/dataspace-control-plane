"""BaSyx Submodel Registry REST client.

Mirrors the BaSyx v3 Submodel Registry OpenAPI spec.
Base path: ``/api/v3.0/submodel-descriptors``.

Submodel IDs in URL path segments must be base64URL-encoded without padding
per AAS Part 2 API specification §3.2.
"""
from __future__ import annotations

import logging
from typing import Any

from ..._shared.http import AsyncAdapterClient
from ..._shared.retries import retry_transient_short
from .config import BasYxSettings
from .errors import BasYxError, SubmodelNotFoundError

logger = logging.getLogger(__name__)

_SM_REGISTRY_BASE = "/api/v3.0"
_SM_DESCRIPTORS = f"{_SM_REGISTRY_BASE}/submodel-descriptors"


class SubmodelRegistryClient:
    """REST client for the BaSyx Submodel Registry API v3.

    Submodel IDs in path parameters must be base64URL-encoded.

    Usage::
        async with SubmodelRegistryClient(cfg) as client:
            descriptors = await client.get_all_submodel_descriptors()
    """

    def __init__(self, cfg: BasYxSettings) -> None:
        self._cfg = cfg
        extra_headers: dict[str, str] = {}
        if cfg.api_key is not None:
            extra_headers["X-API-KEY"] = cfg.api_key.get_secret_value()
        self._http = AsyncAdapterClient(
            str(cfg.submodel_registry_url).rstrip("/"),
            token_provider=None,
            timeout=cfg.request_timeout_s,
            headers=extra_headers,
        )

    async def __aenter__(self) -> "SubmodelRegistryClient":
        await self._http.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._http.__aexit__(*args)

    @retry_transient_short
    async def get_all_submodel_descriptors(self) -> list[dict[str, Any]]:
        """Retrieve all Submodel Descriptors.

        GET /api/v3.0/submodel-descriptors

        Returns:
            List of raw submodel descriptor dicts.
        """
        resp = await self._http.get(_SM_DESCRIPTORS)
        data = resp.json()
        if isinstance(data, dict):
            return data.get("result") or data.get("items") or []
        return data or []

    @retry_transient_short
    async def post_submodel_descriptor(
        self, descriptor: dict[str, Any]
    ) -> dict[str, Any]:
        """Register a new Submodel Descriptor.

        POST /api/v3.0/submodel-descriptors

        Args:
            descriptor: BaSyx-format submodel descriptor dict.

        Returns:
            The created descriptor as returned by the registry.
        """
        resp = await self._http.post(_SM_DESCRIPTORS, json=descriptor)
        result: dict[str, Any] = resp.json()
        logger.debug("Registered submodel descriptor id=%s", descriptor.get("id"))
        return result

    @retry_transient_short
    async def get_submodel_descriptor(self, sm_id_base64: str) -> dict[str, Any]:
        """Retrieve a single Submodel Descriptor by its base64URL-encoded ID.

        GET /api/v3.0/submodel-descriptors/{submodelId}

        Args:
            sm_id_base64: Base64URL-encoded Submodel ID (no padding).

        Returns:
            The submodel descriptor dict.

        Raises:
            SubmodelNotFoundError: If the registry returns HTTP 404.
        """
        try:
            resp = await self._http.get(f"{_SM_DESCRIPTORS}/{sm_id_base64}")
        except Exception as exc:
            from ..._shared.errors import AdapterNotFoundError
            if isinstance(exc, AdapterNotFoundError):
                raise SubmodelNotFoundError(
                    f"Submodel descriptor not found: {sm_id_base64}",
                    upstream_code=404,
                ) from exc
            raise
        return resp.json()

    @retry_transient_short
    async def put_submodel_descriptor(
        self, sm_id_base64: str, descriptor: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing Submodel Descriptor.

        PUT /api/v3.0/submodel-descriptors/{submodelId}

        Args:
            sm_id_base64: Base64URL-encoded Submodel ID (no padding).
            descriptor: Updated submodel descriptor dict.

        Returns:
            The updated descriptor.
        """
        resp = await self._http.put(
            f"{_SM_DESCRIPTORS}/{sm_id_base64}", json=descriptor
        )
        result: dict[str, Any] = resp.json()
        logger.debug("Updated submodel descriptor id=%s", descriptor.get("id"))
        return result

    @retry_transient_short
    async def delete_submodel_descriptor(self, sm_id_base64: str) -> None:
        """Delete a Submodel Descriptor.

        DELETE /api/v3.0/submodel-descriptors/{submodelId}

        Args:
            sm_id_base64: Base64URL-encoded Submodel ID (no padding).
        """
        await self._http.delete(f"{_SM_DESCRIPTORS}/{sm_id_base64}")
        logger.debug("Deleted submodel descriptor sm_id_b64=%s", sm_id_base64)
