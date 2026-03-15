"""Shared transport helpers for checked-in BaSyx generated clients."""
from __future__ import annotations

from typing import Any

from ...._shared.http import AsyncAdapterClient


def basyx_headers(api_key: Any) -> dict[str, str]:
    if api_key is None:
        return {}
    return {"X-API-KEY": api_key.get_secret_value()}


def unwrap_collection(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        result = payload.get("result") or payload.get("items") or []
        return list(result) if isinstance(result, list) else []
    if isinstance(payload, list):
        return list(payload)
    return []


class GeneratedBasyxApiClient:
    """Small transport base used by checked-in generated service stubs."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_s: float,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._http = AsyncAdapterClient(
            base_url.rstrip("/"),
            token_provider=None,
            timeout=timeout_s,
            headers=headers or {},
        )

    async def __aenter__(self) -> "GeneratedBasyxApiClient":
        await self._http.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._http.__aexit__(*args)
