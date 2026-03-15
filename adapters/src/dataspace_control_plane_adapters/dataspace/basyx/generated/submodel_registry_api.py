"""Checked-in generated client for the BaSyx Submodel Registry OpenAPI surface."""
from __future__ import annotations

import logging
from typing import Any

from ...._shared.errors import AdapterNotFoundError
from ...._shared.retries import retry_transient_short
from ..config import BasYxSettings
from ..errors import SubmodelNotFoundError
from ._base import GeneratedBasyxApiClient, basyx_headers, unwrap_collection

logger = logging.getLogger(__name__)

_SM_REGISTRY_BASE = "/api/v3.0"
_SM_DESCRIPTORS = f"{_SM_REGISTRY_BASE}/submodel-descriptors"


class GeneratedSubmodelRegistryApi(GeneratedBasyxApiClient):
    def __init__(self, cfg: BasYxSettings) -> None:
        super().__init__(
            base_url=str(cfg.submodel_registry_url),
            timeout_s=cfg.request_timeout_s,
            headers=basyx_headers(cfg.api_key),
        )

    @retry_transient_short
    async def get_all_submodel_descriptors(self) -> list[dict[str, Any]]:
        response = await self._http.get(_SM_DESCRIPTORS)
        return unwrap_collection(response.json())

    @retry_transient_short
    async def post_submodel_descriptor(
        self,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        response = await self._http.post(_SM_DESCRIPTORS, json=descriptor)
        result: dict[str, Any] = response.json()
        logger.debug("Registered submodel descriptor id=%s", descriptor.get("id"))
        return result

    @retry_transient_short
    async def get_submodel_descriptor(self, sm_id_base64: str) -> dict[str, Any]:
        try:
            response = await self._http.get(f"{_SM_DESCRIPTORS}/{sm_id_base64}")
        except AdapterNotFoundError as exc:
            raise SubmodelNotFoundError(
                f"Submodel descriptor not found: {sm_id_base64}",
                upstream_code=404,
            ) from exc
        return response.json()

    @retry_transient_short
    async def put_submodel_descriptor(
        self,
        sm_id_base64: str,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        response = await self._http.put(
            f"{_SM_DESCRIPTORS}/{sm_id_base64}",
            json=descriptor,
        )
        result: dict[str, Any] = response.json()
        logger.debug("Updated submodel descriptor id=%s", descriptor.get("id"))
        return result

    @retry_transient_short
    async def delete_submodel_descriptor(self, sm_id_base64: str) -> None:
        await self._http.delete(f"{_SM_DESCRIPTORS}/{sm_id_base64}")
        logger.debug("Deleted submodel descriptor sm_id_b64=%s", sm_id_base64)
