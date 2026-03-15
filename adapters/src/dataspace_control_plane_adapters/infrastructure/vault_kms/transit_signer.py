"""Vault Transit signing adapter.

Implements core/domains/machine_trust/ports.py SignerPort using the Vault
Transit secrets engine sign endpoint.

POST /v1/{transit_mount}/sign/{key_name}

Raw private key material never exists in Python — all cryptographic operations
occur inside Vault. Only the signature bytes are returned to the caller.
"""
from __future__ import annotations

import base64
import logging

import httpx

from dataspace_control_plane_adapters._shared.errors import AdapterAuthError, AdapterNotFoundError
from dataspace_control_plane_adapters._shared.retries import retry_transient_short

from .config import VaultSettings
from .errors import VaultAuthError, VaultKeyNotFoundError, VaultTransitError

logger = logging.getLogger(__name__)


def _build_vault_headers(token: str) -> dict[str, str]:
    return {"X-Vault-Token": token, "Content-Type": "application/json"}


class VaultTransitSigner:
    """Signs arbitrary payloads using the Vault Transit secrets engine.

    # implements core/domains/machine_trust/ports.py SignerPort

    The key_id parameter maps to a named key in the Transit engine.  The
    caller is responsible for resolving logical key names to Vault key paths
    via VaultKeyRegistry before calling this class.

    Security contract:
    - The raw token is retrieved from cfg.vault_token.get_secret_value() once
      per call and is never stored as a plain-text attribute.
    - Signature bytes are returned directly; no other secret material is exposed.
    """

    def __init__(self, cfg: VaultSettings) -> None:
        self._cfg = cfg
        self._base_url = str(cfg.vault_addr).rstrip("/")
        self._transit_mount = cfg.transit_mount

    @retry_transient_short
    async def sign(self, payload: bytes, key_id: str) -> bytes:
        """Sign *payload* with the Vault Transit key identified by *key_id*.

        Args:
            payload: Raw bytes to sign.
            key_id:  Name of the Transit key within the configured mount.

        Returns:
            Signature bytes extracted from the Vault ``vault:v1:...`` response.

        Raises:
            VaultKeyNotFoundError: The key does not exist in Vault.
            VaultAuthError: The Vault token is invalid or expired.
            VaultTransitError: Any other Transit engine failure.
        """
        encoded_input = base64.b64encode(payload).decode("ascii")
        url = f"{self._base_url}/v1/{self._transit_mount}/sign/{key_id}"
        body = {
            "input": encoded_input,
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
                raise AdapterTimeoutError(f"Vault sign request timed out for key {key_id!r}") from exc

        if resp.status_code == 403:
            raise VaultAuthError()
        if resp.status_code == 404:
            raise VaultKeyNotFoundError(key_id, self._transit_mount)
        if not resp.is_success:
            raise VaultTransitError(
                f"Vault Transit sign failed for key {key_id!r}: HTTP {resp.status_code} {resp.text[:256]}",
                upstream_code=resp.status_code,
            )

        data = resp.json()
        try:
            vault_signature: str = data["data"]["signature"]
        except (KeyError, TypeError) as exc:
            raise VaultTransitError(
                f"Unexpected Vault Transit sign response shape for key {key_id!r}"
            ) from exc

        # The signature format is "vault:v1:<base64url-encoded-sig>".
        # Strip the prefix and return raw signature bytes.
        parts = vault_signature.split(":", 2)
        if len(parts) != 3:
            raise VaultTransitError(
                f"Unrecognised Vault signature format for key {key_id!r}: {vault_signature[:64]}"
            )
        raw_sig_b64 = parts[2]
        # Vault uses standard base64 (not URL-safe) in JWS marshaling.
        return base64.b64decode(raw_sig_b64 + "==")  # pad to multiple of 4
