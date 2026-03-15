"""BaSyx Submodel Repository REST client.

Mirrors the BaSyx v3 Submodel Repository OpenAPI spec.
Base path: ``/api/v3.0/submodels``.

Supports the standard Submodel CRUD operations plus the AAS-spec ValueOnly
representation for lightweight value access.

Submodel IDs in URL path segments must be base64URL-encoded without padding
per AAS Part 2 API specification §3.2.
"""
from __future__ import annotations

import logging
from typing import Any

from ..._shared.http import AsyncAdapterClient
from ..._shared.retries import retry_transient_short
from .config import BasYxSettings
from .errors import SubmodelNotFoundError

logger = logging.getLogger(__name__)

_SM_REPO_BASE = "/api/v3.0"
_SUBMODELS = f"{_SM_REPO_BASE}/submodels"


class SubmodelRepositoryClient:
    """REST client for the BaSyx Submodel Repository API v3.

    Usage::
        async with SubmodelRepositoryClient(cfg) as client:
            sm = await client.get_submodel(encoded_id)
    """

    def __init__(self, cfg: BasYxSettings) -> None:
        self._cfg = cfg
        extra_headers: dict[str, str] = {}
        if cfg.api_key is not None:
            extra_headers["X-API-KEY"] = cfg.api_key.get_secret_value()
        self._http = AsyncAdapterClient(
            str(cfg.submodel_repository_url).rstrip("/"),
            token_provider=None,
            timeout=cfg.request_timeout_s,
            headers=extra_headers,
        )

    async def __aenter__(self) -> "SubmodelRepositoryClient":
        await self._http.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._http.__aexit__(*args)

    @retry_transient_short
    async def get_all_submodels(
        self, semantic_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve all Submodels, optionally filtered by semanticId.

        GET /api/v3.0/submodels[?semanticId=<base64url>]

        Args:
            semantic_id: Optional semanticId to filter results (raw string, will
                be base64URL-encoded for the query parameter).

        Returns:
            List of raw submodel dicts.
        """
        params: dict[str, str] = {}
        if semantic_id is not None:
            import base64
            encoded = base64.urlsafe_b64encode(semantic_id.encode()).rstrip(b"=").decode()
            params["semanticId"] = encoded
        resp = await self._http.get(_SUBMODELS, params=params)
        data = resp.json()
        if isinstance(data, dict):
            return data.get("result") or data.get("items") or []
        return data or []

    @retry_transient_short
    async def post_submodel(self, submodel: dict[str, Any]) -> dict[str, Any]:
        """Create a new Submodel in the repository.

        POST /api/v3.0/submodels

        Args:
            submodel: AAS v3-format Submodel dict.

        Returns:
            The created Submodel as returned by the repository.
        """
        resp = await self._http.post(_SUBMODELS, json=submodel)
        result: dict[str, Any] = resp.json()
        logger.debug("Created submodel id=%s", submodel.get("id"))
        return result

    @retry_transient_short
    async def get_submodel(self, sm_id_base64: str) -> dict[str, Any]:
        """Retrieve a single Submodel by its base64URL-encoded ID.

        GET /api/v3.0/submodels/{submodelId}

        Args:
            sm_id_base64: Base64URL-encoded Submodel ID (no padding).

        Returns:
            The AAS v3 Submodel dict.

        Raises:
            SubmodelNotFoundError: If the repository returns HTTP 404.
        """
        try:
            resp = await self._http.get(f"{_SUBMODELS}/{sm_id_base64}")
        except Exception as exc:
            from ..._shared.errors import AdapterNotFoundError
            if isinstance(exc, AdapterNotFoundError):
                raise SubmodelNotFoundError(
                    f"Submodel not found: {sm_id_base64}", upstream_code=404
                ) from exc
            raise
        return resp.json()

    @retry_transient_short
    async def put_submodel(
        self, sm_id_base64: str, submodel: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing Submodel.

        PUT /api/v3.0/submodels/{submodelId}

        Args:
            sm_id_base64: Base64URL-encoded Submodel ID (no padding).
            submodel: Updated AAS v3-format Submodel dict.

        Returns:
            The updated Submodel.
        """
        resp = await self._http.put(f"{_SUBMODELS}/{sm_id_base64}", json=submodel)
        result: dict[str, Any] = resp.json()
        logger.debug("Updated submodel sm_id_b64=%s", sm_id_base64)
        return result

    @retry_transient_short
    async def delete_submodel(self, sm_id_base64: str) -> None:
        """Delete a Submodel from the repository.

        DELETE /api/v3.0/submodels/{submodelId}

        Args:
            sm_id_base64: Base64URL-encoded Submodel ID (no padding).
        """
        await self._http.delete(f"{_SUBMODELS}/{sm_id_base64}")
        logger.debug("Deleted submodel sm_id_b64=%s", sm_id_base64)

    @retry_transient_short
    async def get_submodel_value(self, sm_id_base64: str) -> dict[str, Any]:
        """Retrieve the ValueOnly representation of a Submodel.

        GET /api/v3.0/submodels/{submodelId}/$value

        The ValueOnly representation is a flat JSON projection of submodel
        element values as specified in AAS Part 2 §9.

        Args:
            sm_id_base64: Base64URL-encoded Submodel ID (no padding).

        Returns:
            ValueOnly dict — flat key/value pairs of submodel element values.

        Raises:
            SubmodelNotFoundError: If the repository returns HTTP 404.
        """
        try:
            resp = await self._http.get(f"{_SUBMODELS}/{sm_id_base64}/$value")
        except Exception as exc:
            from ..._shared.errors import AdapterNotFoundError
            if isinstance(exc, AdapterNotFoundError):
                raise SubmodelNotFoundError(
                    f"Submodel value not found: {sm_id_base64}", upstream_code=404
                ) from exc
            raise
        result: dict[str, Any] = resp.json()
        logger.debug("Fetched ValueOnly for sm_id_b64=%s", sm_id_base64)
        return result
