"""Thin wrapper over the checked-in generated BaSyx AAS Registry client."""
from __future__ import annotations

from typing import Any

from .config import BasYxSettings
from .generated import GeneratedAasRegistryApi


class AasRegistryClient:
    """Stable adapter entry point for the BaSyx AAS Registry API."""

    def __init__(self, cfg: BasYxSettings) -> None:
        self._generated = GeneratedAasRegistryApi(cfg)

    async def __aenter__(self) -> "AasRegistryClient":
        await self._generated.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._generated.__aexit__(*args)

    async def get_all_shell_descriptors(self) -> list[dict[str, Any]]:
        return await self._generated.get_all_shell_descriptors()

    async def post_shell_descriptor(self, descriptor: dict[str, Any]) -> dict[str, Any]:
        return await self._generated.post_shell_descriptor(descriptor)

    async def get_shell_descriptor(self, aas_id_base64: str) -> dict[str, Any]:
        return await self._generated.get_shell_descriptor(aas_id_base64)

    async def put_shell_descriptor(
        self,
        aas_id_base64: str,
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._generated.put_shell_descriptor(aas_id_base64, descriptor)

    async def delete_shell_descriptor(self, aas_id_base64: str) -> None:
        await self._generated.delete_shell_descriptor(aas_id_base64)
