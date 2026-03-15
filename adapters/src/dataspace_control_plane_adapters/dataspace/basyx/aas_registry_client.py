"""BaSyx AAS Registry REST client.

Structured as a hand-written client mirroring the BaSyx v3 AAS Registry
OpenAPI spec (/v3/api-docs). Base path: ``/api/v3.0/shell-descriptors``.

AAS IDs used in URL path segments MUST be base64URL-encoded without padding
per AAS Part 2 API specification §3.2. Use descriptor_mappers.encode_aas_id().
"""
from __future__ import annotations

import logging
from typing import Any

from ..._shared.auth import ApiKeyToken, StaticTokenProvider
from ..._shared.http import AsyncAdapterClient
from ..._shared.retries import retry_transient_short
from .config import BasYxSettings
from .errors import AasDescriptorNotFoundError, BasYxError

logger = logging.getLogger(__name__)

_AAS_REGISTRY_BASE = "/api/v3.0"
_SHELL_DESCRIPTORS = f"{_AAS_REGISTRY_BASE}/shell-descriptors"


class AasRegistryClient:
    """REST client for the BaSyx AAS Registry API v3.

    All AAS IDs in URL path parameters must be base64URL-encoded.
    Use descriptor_mappers.encode_aas_id() before passing to path-based methods.

    Usage::
        async with AasRegistryClient(cfg) as client:
            descriptors = await client.get_all_shell_descriptors()
    """

    def __init__(self, cfg: BasYxSettings) -> None:
        self._cfg = cfg
        token_provider = None
        if cfg.api_key is not None:
            token_provider = StaticTokenProvider(cfg.api_key.get_secret_value())
        extra_headers: dict[str, str] = {}
        if cfg.api_key is not None:
            extra_headers["X-API-KEY"] = cfg.api_key.get_secret_value()
        self._http = AsyncAdapterClient(
            str(cfg.aas_registry_url).rstrip("/"),
            token_provider=None,  # AAS Registry uses X-API-KEY, not Bearer
            timeout=cfg.request_timeout_s,
            headers=extra_headers,
        )

    async def __aenter__(self) -> "AasRegistryClient":
        await self._http.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._http.__aexit__(*args)

    @retry_transient_short
    async def get_all_shell_descriptors(self) -> list[dict[str, Any]]:
        """Retrieve all AAS Shell Descriptors from the registry.

        GET /api/v3.0/shell-descriptors

        Returns:
            List of raw shell descriptor dicts.
        """
        resp = await self._http.get(_SHELL_DESCRIPTORS)
        data = resp.json()
        # BaSyx v3 may wrap results in {"result": [...]} or return a plain list.
        if isinstance(data, dict):
            return data.get("result") or data.get("items") or []
        return data or []

    @retry_transient_short
    async def post_shell_descriptor(self, descriptor: dict[str, Any]) -> dict[str, Any]:
        """Register a new AAS Shell Descriptor.

        POST /api/v3.0/shell-descriptors

        Args:
            descriptor: BaSyx-format shell descriptor dict.

        Returns:
            The created descriptor as returned by the registry.
        """
        resp = await self._http.post(_SHELL_DESCRIPTORS, json=descriptor)
        result: dict[str, Any] = resp.json()
        logger.debug("Registered shell descriptor id=%s", descriptor.get("id"))
        return result

    @retry_transient_short
    async def get_shell_descriptor(self, aas_id_base64: str) -> dict[str, Any]:
        """Retrieve a single AAS Shell Descriptor by its base64URL-encoded ID.

        GET /api/v3.0/shell-descriptors/{aasId}

        Args:
            aas_id_base64: Base64URL-encoded AAS ID (no padding).

        Returns:
            The shell descriptor dict.

        Raises:
            AasDescriptorNotFoundError: If the registry returns HTTP 404.
        """
        try:
            resp = await self._http.get(f"{_SHELL_DESCRIPTORS}/{aas_id_base64}")
        except Exception as exc:
            from ..._shared.errors import AdapterNotFoundError
            if isinstance(exc, AdapterNotFoundError):
                raise AasDescriptorNotFoundError(
                    f"AAS shell descriptor not found: {aas_id_base64}",
                    upstream_code=404,
                ) from exc
            raise
        return resp.json()

    @retry_transient_short
    async def put_shell_descriptor(
        self, aas_id_base64: str, descriptor: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing AAS Shell Descriptor.

        PUT /api/v3.0/shell-descriptors/{aasId}

        Args:
            aas_id_base64: Base64URL-encoded AAS ID (no padding).
            descriptor: Updated BaSyx-format shell descriptor dict.

        Returns:
            The updated descriptor as returned by the registry.
        """
        resp = await self._http.put(
            f"{_SHELL_DESCRIPTORS}/{aas_id_base64}", json=descriptor
        )
        result: dict[str, Any] = resp.json()
        logger.debug("Updated shell descriptor id=%s", descriptor.get("id"))
        return result

    @retry_transient_short
    async def delete_shell_descriptor(self, aas_id_base64: str) -> None:
        """Delete an AAS Shell Descriptor.

        DELETE /api/v3.0/shell-descriptors/{aasId}

        Args:
            aas_id_base64: Base64URL-encoded AAS ID (no padding).
        """
        await self._http.delete(f"{_SHELL_DESCRIPTORS}/{aas_id_base64}")
        logger.debug("Deleted shell descriptor aas_id_b64=%s", aas_id_base64)
