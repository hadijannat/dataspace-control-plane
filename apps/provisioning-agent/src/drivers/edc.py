"""
EDC Management API driver stub.
Use for connector registration/configuration during bootstrap.
Thin — does not embed business logic.
"""
import httpx
import structlog
from typing import Any

logger = structlog.get_logger(__name__)


class EDCDriver:
    def __init__(self, management_url: str, api_key: str) -> None:
        self._management_url = management_url.rstrip("/")
        self._http = httpx.AsyncClient(
            timeout=30.0,
            headers={"x-api-key": api_key},
        )

    async def health_check(self) -> bool:
        try:
            resp = await self._http.get(f"{self._management_url}/check/health")
            return resp.status_code == 200
        except httpx.ConnectError:
            return False

    async def close(self) -> None:
        await self._http.aclose()
