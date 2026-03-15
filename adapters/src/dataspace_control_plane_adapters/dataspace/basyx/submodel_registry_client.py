"""Thin wrapper over the checked-in generated BaSyx Submodel Registry client."""
from __future__ import annotations

from typing import Any

from .config import BasYxSettings
from .generated import GeneratedSubmodelRegistryApi


class SubmodelRegistryClient:
    """Stable adapter entry point for the BaSyx Submodel Registry API."""

    def __init__(self, cfg: BasYxSettings) -> None:
        self._generated = GeneratedSubmodelRegistryApi(cfg)

    async def __aenter__(self) -> "SubmodelRegistryClient":
        await self._generated.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._generated.__aexit__(*args)

    async def get_all_submodel_descriptors(self) -> list[dict[str, Any]]:
        return await self._generated.get_all_submodel_descriptors()

    async def post_submodel_descriptor(
        self,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._generated.post_submodel_descriptor(descriptor)

    async def get_submodel_descriptor(self, sm_id_base64: str) -> dict[str, Any]:
        return await self._generated.get_submodel_descriptor(sm_id_base64)

    async def put_submodel_descriptor(
        self,
        sm_id_base64: str,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._generated.put_submodel_descriptor(sm_id_base64, descriptor)

    async def delete_submodel_descriptor(self, sm_id_base64: str) -> None:
        await self._generated.delete_submodel_descriptor(sm_id_base64)
