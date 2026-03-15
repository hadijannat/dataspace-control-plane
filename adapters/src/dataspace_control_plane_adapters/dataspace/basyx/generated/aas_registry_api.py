"""Checked-in generated client for the BaSyx AAS Registry OpenAPI surface."""
from __future__ import annotations

import logging
from typing import Any

from ...._shared.errors import AdapterNotFoundError
from ...._shared.retries import retry_transient_short
from ..config import BasYxSettings
from ..errors import AasDescriptorNotFoundError
from ._base import GeneratedBasyxApiClient, basyx_headers, unwrap_collection

logger = logging.getLogger(__name__)

_AAS_REGISTRY_BASE = "/api/v3.0"
_SHELL_DESCRIPTORS = f"{_AAS_REGISTRY_BASE}/shell-descriptors"


class GeneratedAasRegistryApi(GeneratedBasyxApiClient):
    def __init__(self, cfg: BasYxSettings) -> None:
        super().__init__(
            base_url=str(cfg.aas_registry_url),
            timeout_s=cfg.request_timeout_s,
            headers=basyx_headers(cfg.api_key),
        )

    @retry_transient_short
    async def get_all_shell_descriptors(self) -> list[dict[str, Any]]:
        response = await self._http.get(_SHELL_DESCRIPTORS)
        return unwrap_collection(response.json())

    @retry_transient_short
    async def post_shell_descriptor(self, descriptor: dict[str, Any]) -> dict[str, Any]:
        response = await self._http.post(_SHELL_DESCRIPTORS, json=descriptor)
        result: dict[str, Any] = response.json()
        logger.debug("Registered shell descriptor id=%s", descriptor.get("id"))
        return result

    @retry_transient_short
    async def get_shell_descriptor(self, aas_id_base64: str) -> dict[str, Any]:
        try:
            response = await self._http.get(f"{_SHELL_DESCRIPTORS}/{aas_id_base64}")
        except AdapterNotFoundError as exc:
            raise AasDescriptorNotFoundError(
                f"AAS shell descriptor not found: {aas_id_base64}",
                upstream_code=404,
            ) from exc
        return response.json()

    @retry_transient_short
    async def put_shell_descriptor(
        self,
        aas_id_base64: str,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        response = await self._http.put(
            f"{_SHELL_DESCRIPTORS}/{aas_id_base64}",
            json=descriptor,
        )
        result: dict[str, Any] = response.json()
        logger.debug("Updated shell descriptor id=%s", descriptor.get("id"))
        return result

    @retry_transient_short
    async def delete_shell_descriptor(self, aas_id_base64: str) -> None:
        await self._http.delete(f"{_SHELL_DESCRIPTORS}/{aas_id_base64}")
        logger.debug("Deleted shell descriptor aas_id_b64=%s", aas_id_base64)
