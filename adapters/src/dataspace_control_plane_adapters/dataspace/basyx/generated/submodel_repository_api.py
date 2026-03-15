"""Checked-in generated client for the BaSyx Submodel Repository OpenAPI surface."""
from __future__ import annotations

import base64
import logging
from typing import Any

from ...._shared.errors import AdapterNotFoundError
from ...._shared.retries import retry_transient_short
from ..config import BasYxSettings
from ..errors import SubmodelNotFoundError
from ._base import GeneratedBasyxApiClient, basyx_headers, unwrap_collection

logger = logging.getLogger(__name__)

_SM_REPO_BASE = "/api/v3.0"
_SUBMODELS = f"{_SM_REPO_BASE}/submodels"


class GeneratedSubmodelRepositoryApi(GeneratedBasyxApiClient):
    def __init__(self, cfg: BasYxSettings) -> None:
        super().__init__(
            base_url=str(cfg.submodel_repository_url),
            timeout_s=cfg.request_timeout_s,
            headers=basyx_headers(cfg.api_key),
        )

    @retry_transient_short
    async def get_all_submodels(
        self,
        semantic_id: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if semantic_id is not None:
            encoded = (
                base64.urlsafe_b64encode(semantic_id.encode())
                .rstrip(b"=")
                .decode()
            )
            params["semanticId"] = encoded
        response = await self._http.get(_SUBMODELS, params=params)
        return unwrap_collection(response.json())

    @retry_transient_short
    async def post_submodel(self, submodel: dict[str, Any]) -> dict[str, Any]:
        response = await self._http.post(_SUBMODELS, json=submodel)
        result: dict[str, Any] = response.json()
        logger.debug("Created submodel id=%s", submodel.get("id"))
        return result

    @retry_transient_short
    async def get_submodel(self, sm_id_base64: str) -> dict[str, Any]:
        try:
            response = await self._http.get(f"{_SUBMODELS}/{sm_id_base64}")
        except AdapterNotFoundError as exc:
            raise SubmodelNotFoundError(
                f"Submodel not found: {sm_id_base64}",
                upstream_code=404,
            ) from exc
        return response.json()

    @retry_transient_short
    async def put_submodel(
        self,
        sm_id_base64: str,
        submodel: dict[str, Any],
    ) -> dict[str, Any]:
        response = await self._http.put(f"{_SUBMODELS}/{sm_id_base64}", json=submodel)
        result: dict[str, Any] = response.json()
        logger.debug("Updated submodel sm_id_b64=%s", sm_id_base64)
        return result

    @retry_transient_short
    async def delete_submodel(self, sm_id_base64: str) -> None:
        await self._http.delete(f"{_SUBMODELS}/{sm_id_base64}")
        logger.debug("Deleted submodel sm_id_b64=%s", sm_id_base64)

    @retry_transient_short
    async def get_submodel_value(self, sm_id_base64: str) -> dict[str, Any]:
        try:
            response = await self._http.get(f"{_SUBMODELS}/{sm_id_base64}/$value")
        except AdapterNotFoundError as exc:
            raise SubmodelNotFoundError(
                f"Submodel value not found: {sm_id_base64}",
                upstream_code=404,
            ) from exc
        result: dict[str, Any] = response.json()
        logger.debug("Fetched ValueOnly for sm_id_b64=%s", sm_id_base64)
        return result
