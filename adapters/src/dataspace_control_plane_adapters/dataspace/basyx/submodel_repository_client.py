"""Thin wrapper over the checked-in generated BaSyx Submodel Repository client."""
from __future__ import annotations

from typing import Any

from .config import BasYxSettings
from .generated import GeneratedSubmodelRepositoryApi


class SubmodelRepositoryClient:
    """Stable adapter entry point for the BaSyx Submodel Repository API."""

    def __init__(self, cfg: BasYxSettings) -> None:
        self._generated = GeneratedSubmodelRepositoryApi(cfg)

    async def __aenter__(self) -> "SubmodelRepositoryClient":
        await self._generated.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._generated.__aexit__(*args)

    async def get_all_submodels(
        self,
        semantic_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._generated.get_all_submodels(semantic_id)

    async def post_submodel(self, submodel: dict[str, Any]) -> dict[str, Any]:
        return await self._generated.post_submodel(submodel)

    async def get_submodel(self, sm_id_base64: str) -> dict[str, Any]:
        return await self._generated.get_submodel(sm_id_base64)

    async def put_submodel(
        self,
        sm_id_base64: str,
        submodel: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._generated.put_submodel(sm_id_base64, submodel)

    async def delete_submodel(self, sm_id_base64: str) -> None:
        await self._generated.delete_submodel(sm_id_base64)

    async def get_submodel_value(self, sm_id_base64: str) -> dict[str, Any]:
        return await self._generated.get_submodel_value(sm_id_base64)
