"""Vault PKI certificate issuer.

Issues short-lived X.509 certificates via the Vault PKI secrets engine.

POST /v1/{pki_mount}/issue/{pki_role}

Security contract:
- The private_key returned in the response is ephemeral. Callers MUST NOT
  persist it to disk, databases, logs, or workflow state.
- The certificate PEM may be stored; the private key may only live in memory
  for the duration of the mTLS handshake or session setup.
"""
from __future__ import annotations

import logging

import httpx

from dataspace_control_plane_adapters._shared.retries import retry_transient_short

from .config import VaultSettings
from .errors import VaultAuthError, VaultPkiError

logger = logging.getLogger(__name__)


def _build_vault_headers(token: str) -> dict[str, str]:
    return {"X-Vault-Token": token, "Content-Type": "application/json"}


class VaultPkiIssuer:
    """Issues X.509 certificates via the Vault PKI engine.

    Certificates are short-lived. Callers should use CertificateLifecycleManager
    to track expiry and trigger renewal before the certificate expires.
    """

    def __init__(self, cfg: VaultSettings) -> None:
        self._cfg = cfg
        self._base_url = str(cfg.vault_addr).rstrip("/")
        self._pki_mount = cfg.pki_mount
        self._pki_role = cfg.pki_role

    @retry_transient_short
    async def issue_cert(
        self,
        common_name: str,
        ttl: str = "24h",
        alt_names: list[str] | None = None,
        ip_sans: list[str] | None = None,
    ) -> dict[str, str]:
        """Issue a new X.509 certificate for *common_name*.

        Args:
            common_name: Subject CN for the certificate (e.g. service FQDN or DID).
            ttl:         Certificate lifetime in Vault duration format (e.g. ``"24h"``).
            alt_names:   Optional list of DNS Subject Alternative Names.
            ip_sans:     Optional list of IP Subject Alternative Names.

        Returns:
            Dictionary with keys:
            - ``certificate``: PEM-encoded X.509 certificate.
            - ``private_key``: PEM-encoded private key (EPHEMERAL — do not persist).
            - ``serial_number``: Certificate serial number string.
            - ``ca_chain``: List of issuing CA PEM strings joined by newline.

        Raises:
            VaultAuthError: Invalid Vault credentials.
            VaultPkiError:  Any other PKI engine failure.

        Important:
            The ``private_key`` in the response is ephemeral. The caller MUST NOT
            write it to disk, databases, logs, or any persistent storage.
        """
        url = f"{self._base_url}/v1/{self._pki_mount}/issue/{self._pki_role}"
        body: dict[str, object] = {"common_name": common_name, "ttl": ttl}
        if alt_names:
            body["alt_names"] = ",".join(alt_names)
        if ip_sans:
            body["ip_sans"] = ",".join(ip_sans)

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
                    f"Vault PKI issue request timed out for CN={common_name!r}"
                ) from exc

        if resp.status_code == 403:
            raise VaultAuthError()
        if not resp.is_success:
            raise VaultPkiError(
                f"Vault PKI issue failed for CN={common_name!r}: HTTP {resp.status_code} {resp.text[:256]}",
                upstream_code=resp.status_code,
            )

        data = resp.json()
        try:
            cert_data = data["data"]
            ca_chain_list: list[str] = cert_data.get("ca_chain", [])
            return {
                "certificate": cert_data["certificate"],
                "private_key": cert_data["private_key"],  # EPHEMERAL
                "serial_number": cert_data["serial_number"],
                "ca_chain": "\n".join(ca_chain_list),
            }
        except (KeyError, TypeError) as exc:
            raise VaultPkiError(
                f"Unexpected Vault PKI issue response shape for CN={common_name!r}"
            ) from exc
