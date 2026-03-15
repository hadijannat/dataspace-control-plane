"""
Control API driver.
Uses the public procedure endpoints so provisioning work is accepted by the
control plane before it is checkpointed locally.
"""
from __future__ import annotations

from typing import Any

import httpx


class ControlApiDriver:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=30.0,
            headers=headers,
        )

    async def start_procedure(self, body: dict[str, Any]) -> dict[str, Any]:
        response = await self._http.post("/api/v1/public/procedures/start", json=body)
        response.raise_for_status()
        return response.json()

    async def get_procedure_status(self, workflow_id: str) -> dict[str, Any]:
        response = await self._http.get(f"/api/v1/public/procedures/{workflow_id}")
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._http.aclose()

