"""
HashiCorp Vault driver stub.
Resolves secret references like vault:secret/data/keycloak/web-console-secret.
Never surfaces raw secret values in logs or diffs.
"""
import httpx
import structlog

logger = structlog.get_logger(__name__)


class VaultDriver:
    def __init__(self, vault_addr: str, vault_token: str) -> None:
        self._addr = vault_addr.rstrip("/")
        self._http = httpx.AsyncClient(
            timeout=10.0,
            headers={"X-Vault-Token": vault_token},
        )

    async def read_secret(self, path: str) -> dict:
        """Read a KV v2 secret. path is like 'secret/data/keycloak/web-console-secret'."""
        resp = await self._http.get(f"{self._addr}/v1/{path}")
        resp.raise_for_status()
        return resp.json()["data"]["data"]

    async def close(self) -> None:
        await self._http.aclose()
