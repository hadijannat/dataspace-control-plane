"""Vault Transit verification adapter.

Uses the Vault Transit verify endpoint to check that a given signature was
produced by the named key.

POST /v1/{transit_mount}/verify/{key_name}

All cryptographic verification occurs inside Vault; no private key material
ever exists in Python code.
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


class VaultTransitVerifier:
    """Verifies signatures produced by the Vault Transit engine.

    This class does NOT implement a core port directly; it is a helper used
    by PresentationVerifierPort implementations that delegate cryptographic
    checks to Vault.
    """

    def __init__(self, cfg: VaultSettings) -> None:
        self._cfg = cfg
        self._base_url = str(cfg.vault_addr).rstrip("/")
        self._transit_mount = cfg.transit_mount

    @retry_transient_short
    async def verify(self, payload: bytes, signature: str, key_id: str) -> bool:
        """Verify that *signature* was produced by the Transit key *key_id* over *payload*.

        Args:
            payload:   Original plaintext bytes that were signed.
            signature: Vault-formatted signature string (``vault:v1:...``).
            key_id:    Name of the Transit key within the configured mount.

        Returns:
            True if the signature is valid, False otherwise.

        Raises:
            VaultKeyNotFoundError: The key does not exist in Vault.
            VaultAuthError: The Vault token is invalid or expired.
            VaultTransitError: Any other Transit engine failure.
        """
        encoded_input = base64.b64encode(payload).decode("ascii")
        url = f"{self._base_url}/v1/{self._transit_mount}/verify/{key_id}"
        body = {
            "input": encoded_input,
            "signature": signature,
            "marshaling_algorithm": "jws",
        }
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
                    f"Vault verify request timed out for key {key_id!r}"
                ) from exc

        if resp.status_code == 403:
            raise VaultAuthError()
        if resp.status_code == 404:
            raise VaultKeyNotFoundError(key_id, self._transit_mount)
        if not resp.is_success:
            raise VaultTransitError(
                f"Vault Transit verify failed for key {key_id!r}: HTTP {resp.status_code} {resp.text[:256]}",
                upstream_code=resp.status_code,
            )

        data = resp.json()
        try:
            return bool(data["data"]["valid"])
        except (KeyError, TypeError) as exc:
            raise VaultTransitError(
                f"Unexpected Vault Transit verify response shape for key {key_id!r}"
            ) from exc
