"""Vault Transit HMAC adapter.

Generates and verifies HMAC proof material using the Vault Transit engine.

POST /v1/{transit_mount}/hmac/{key_name}      — generate HMAC
POST /v1/{transit_mount}/verify/{key_name}    — verify HMAC (same verify endpoint)

Use cases: integrity checks on audit records, idempotency keys, proof-of-receipt tokens.
All HMAC operations occur inside Vault; no key material leaves the server.
"""
from __future__ import annotations

import base64
import logging

import httpx

from dataspace_control_plane_adapters._shared.retries import retry_transient_short

from .config import VaultSettings
from .errors import VaultAuthError, VaultKeyNotFoundError, VaultTransitError

logger = logging.getLogger(__name__)


def _build_vault_headers(token: str) -> dict[str, str]:
    return {"X-Vault-Token": token, "Content-Type": "application/json"}


class VaultTransitHmac:
    """Generates and verifies HMAC tokens via the Vault Transit engine.

    Returned HMAC strings follow the Vault format: ``vault:v1:<base64>``.
    """

    def __init__(self, cfg: VaultSettings) -> None:
        self._cfg = cfg
        self._base_url = str(cfg.vault_addr).rstrip("/")
        self._transit_mount = cfg.transit_mount

    @retry_transient_short
    async def hmac(self, payload: bytes, key_id: str) -> str:
        """Compute an HMAC over *payload* using the Transit key *key_id*.

        Args:
            payload: Bytes to authenticate.
            key_id:  Name of the Transit key (must be an HMAC-capable key type).

        Returns:
            Vault-formatted HMAC string (``vault:v1:...``).

        Raises:
            VaultKeyNotFoundError: The key does not exist.
            VaultAuthError: Invalid Vault credentials.
            VaultTransitError: Any other Transit engine failure.
        """
        encoded_input = base64.b64encode(payload).decode("ascii")
        url = f"{self._base_url}/v1/{self._transit_mount}/hmac/{key_id}"
        body = {"input": encoded_input}
        headers = _build_vault_headers(self._cfg.vault_token.get_secret_value())

        async with httpx.AsyncClient(
            timeout=self._cfg.request_timeout_s,
            verify=self._cfg.tls_verify,
        ) as client:
            try:
                resp = await client.post(url, json=body, headers=headers)
            except httpx.ConnectError as exc:
                from dataspace_control_plane_adapters._shared.errors import AdapterUnavailableError
                raise AdapterUnavailableError(f"Cannot reach Vault at {self._base_url}") from exc
            except httpx.TimeoutException as exc:
                from dataspace_control_plane_adapters._shared.errors import AdapterTimeoutError
                raise AdapterTimeoutError(
                    f"Vault hmac request timed out for key {key_id!r}"
                ) from exc

        if resp.status_code == 403:
            raise VaultAuthError()
        if resp.status_code == 404:
            raise VaultKeyNotFoundError(key_id, self._transit_mount)
        if not resp.is_success:
            raise VaultTransitError(
                f"Vault Transit hmac failed for key {key_id!r}: HTTP {resp.status_code} {resp.text[:256]}",
                upstream_code=resp.status_code,
            )

        data = resp.json()
        try:
            return str(data["data"]["hmac"])
        except (KeyError, TypeError) as exc:
            raise VaultTransitError(
                f"Unexpected Vault Transit hmac response shape for key {key_id!r}"
            ) from exc

    @retry_transient_short
    async def verify_hmac(self, payload: bytes, key_id: str, hmac_str: str) -> bool:
        """Verify that *hmac_str* is a valid HMAC over *payload* for key *key_id*.

        Args:
            payload:  Original bytes that were authenticated.
            key_id:   Transit key used to produce the HMAC.
            hmac_str: Vault HMAC string to verify (``vault:v1:...``).

        Returns:
            True if the HMAC is valid, False otherwise.

        Raises:
            VaultKeyNotFoundError: The key does not exist.
            VaultAuthError: Invalid Vault credentials.
            VaultTransitError: Any other Transit engine failure.
        """
        encoded_input = base64.b64encode(payload).decode("ascii")
        # Vault uses the same /verify endpoint for both signatures and HMACs.
        url = f"{self._base_url}/v1/{self._transit_mount}/verify/{key_id}"
        body = {"input": encoded_input, "hmac": hmac_str}
        headers = _build_vault_headers(self._cfg.vault_token.get_secret_value())

        async with httpx.AsyncClient(
            timeout=self._cfg.request_timeout_s,
            verify=self._cfg.tls_verify,
        ) as client:
            try:
                resp = await client.post(url, json=body, headers=headers)
            except httpx.ConnectError as exc:
                from dataspace_control_plane_adapters._shared.errors import AdapterUnavailableError
                raise AdapterUnavailableError(f"Cannot reach Vault at {self._base_url}") from exc
            except httpx.TimeoutException as exc:
                from dataspace_control_plane_adapters._shared.errors import AdapterTimeoutError
                raise AdapterTimeoutError(
                    f"Vault verify_hmac request timed out for key {key_id!r}"
                ) from exc

        if resp.status_code == 403:
            raise VaultAuthError()
        if resp.status_code == 404:
            raise VaultKeyNotFoundError(key_id, self._transit_mount)
        if not resp.is_success:
            raise VaultTransitError(
                f"Vault Transit verify_hmac failed for key {key_id!r}: HTTP {resp.status_code} {resp.text[:256]}",
                upstream_code=resp.status_code,
            )

        data = resp.json()
        try:
            return bool(data["data"]["valid"])
        except (KeyError, TypeError) as exc:
            raise VaultTransitError(
                f"Unexpected Vault Transit verify_hmac response shape for key {key_id!r}"
            ) from exc
