"""
Keycloak Admin REST driver.
Uses Admin REST API for realm/client/role management.
All operations are idempotent (check-before-create pattern).
"""
import httpx
import structlog
from typing import Any

logger = structlog.get_logger(__name__)


class KeycloakAdminDriver:
    def __init__(self, base_url: str, realm: str, client_id: str, client_secret: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._realm = realm
        self._client_id = client_id
        self._client_secret = client_secret
        self._token: str | None = None
        self._http = httpx.AsyncClient(timeout=30.0)

    async def _get_token(self) -> str:
        resp = await self._http.post(
            f"{self._base_url}/realms/{self._realm}/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    async def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            self._token = await self._get_token()
        return {"Authorization": f"Bearer {self._token}"}

    async def realm_exists(self, realm: str) -> bool:
        headers = await self._auth_headers()
        resp = await self._http.get(f"{self._base_url}/admin/realms/{realm}", headers=headers)
        return resp.status_code == 200

    async def get_realm(self, realm: str) -> dict[str, Any] | None:
        headers = await self._auth_headers()
        resp = await self._http.get(f"{self._base_url}/admin/realms/{realm}", headers=headers)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    async def create_realm(self, realm: str, display_name: str, enabled: bool = True) -> None:
        headers = await self._auth_headers()
        logger.info("keycloak.create_realm", realm=realm)
        resp = await self._http.post(
            f"{self._base_url}/admin/realms",
            json={"realm": realm, "displayName": display_name, "enabled": enabled},
            headers=headers,
        )
        resp.raise_for_status()

    async def list_client_ids(self, realm: str) -> list[str]:
        headers = await self._auth_headers()
        resp = await self._http.get(
            f"{self._base_url}/admin/realms/{realm}/clients",
            headers=headers,
        )
        resp.raise_for_status()
        return [item["clientId"] for item in resp.json()]

    async def client_exists(self, realm: str, client_id: str) -> bool:
        headers = await self._auth_headers()
        resp = await self._http.get(
            f"{self._base_url}/admin/realms/{realm}/clients",
            params={"clientId": client_id},
            headers=headers,
        )
        resp.raise_for_status()
        return len(resp.json()) > 0

    async def create_client(self, realm: str, spec: dict[str, Any]) -> None:
        headers = await self._auth_headers()
        logger.info("keycloak.create_client", realm=realm, client_id=spec.get("clientId"))
        resp = await self._http.post(
            f"{self._base_url}/admin/realms/{realm}/clients",
            json=spec,
            headers=headers,
        )
        resp.raise_for_status()

    async def close(self) -> None:
        await self._http.aclose()
