"""Certificate lifecycle management via Vault PKI engine.

Handles revocation, tidy operations, and renewal-readiness checks for
certificates issued through VaultPkiIssuer.

Vault API endpoints used:
  POST /v1/{pki_mount}/revoke   — revoke by serial number
  POST /v1/{pki_mount}/tidy     — clean up expired certificates and CRLs
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from dataspace_control_plane_adapters._shared.retries import retry_transient_short

from .config import VaultSettings
from .errors import VaultAuthError, VaultPkiError

logger = logging.getLogger(__name__)


def _build_vault_headers(token: str) -> dict[str, str]:
    return {"X-Vault-Token": token, "Content-Type": "application/json"}


class CertificateLifecycleManager:
    """Manages revocation, tidy, and renewal scheduling for PKI certificates."""

    def __init__(self, cfg: VaultSettings) -> None:
        self._cfg = cfg
        self._base_url = str(cfg.vault_addr).rstrip("/")
        self._pki_mount = cfg.pki_mount

    @retry_transient_short
    async def revoke(self, serial_number: str) -> None:
        """Revoke a certificate by its serial number.

        Args:
            serial_number: Certificate serial number as returned by Vault PKI
                           (colon-separated hex, e.g. ``"1a:2b:3c:..."``).

        Raises:
            VaultAuthError: Invalid Vault credentials.
            VaultPkiError:  Vault returned an error for the revoke operation.
        """
        url = f"{self._base_url}/v1/{self._pki_mount}/revoke"
        body = {"serial_number": serial_number}
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
                    f"Vault PKI revoke timed out for serial {serial_number!r}"
                ) from exc

        if resp.status_code == 403:
            raise VaultAuthError()
        if not resp.is_success:
            raise VaultPkiError(
                f"Vault PKI revoke failed for serial {serial_number!r}: "
                f"HTTP {resp.status_code} {resp.text[:256]}",
                upstream_code=resp.status_code,
            )
        logger.info("Revoked certificate serial=%s", serial_number)

    @retry_transient_short
    async def tidy(
        self,
        *,
        tidy_cert_store: bool = True,
        tidy_revoked_certs: bool = True,
        safety_buffer: str = "72h",
    ) -> None:
        """Trigger a PKI tidy operation to clean up expired certificates and CRLs.

        Args:
            tidy_cert_store:    Remove expired certificates from the store.
            tidy_revoked_certs: Remove revoked certificates past their expiry.
            safety_buffer:      Extra buffer before removing expired certs (Vault duration string).

        Raises:
            VaultAuthError: Invalid Vault credentials.
            VaultPkiError:  Vault returned an error for the tidy operation.
        """
        url = f"{self._base_url}/v1/{self._pki_mount}/tidy"
        body = {
            "tidy_cert_store": tidy_cert_store,
            "tidy_revoked_certs": tidy_revoked_certs,
            "safety_buffer": safety_buffer,
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
                raise AdapterTimeoutError("Vault PKI tidy request timed out") from exc

        if resp.status_code == 403:
            raise VaultAuthError()
        # Vault returns 202 Accepted for async tidy; treat any 2xx as success.
        if not resp.is_success:
            raise VaultPkiError(
                f"Vault PKI tidy failed: HTTP {resp.status_code} {resp.text[:256]}",
                upstream_code=resp.status_code,
            )
        logger.info("Vault PKI tidy initiated (status=%s)", resp.status_code)

    @staticmethod
    async def should_renew(cert_pem: str, renew_before_expiry_s: int = 86400) -> bool:
        """Return True if the certificate should be renewed based on its expiry.

        Parses the ``notAfter`` field from the PEM certificate and returns True
        when the remaining lifetime is less than *renew_before_expiry_s* seconds.

        Args:
            cert_pem:              PEM-encoded X.509 certificate string.
            renew_before_expiry_s: Seconds before expiry to trigger renewal
                                   (default: 86400 = 24 hours).

        Returns:
            True if renewal is recommended, False otherwise.

        Raises:
            ValueError: If the PEM cannot be parsed or has no ``notAfter`` field.
        """
        # Heavy SDK import deferred to avoid mandatory dependency at module load time.
        # TODO: production impl — consider using the ``cryptography`` library for robust parsing
        from cryptography import x509  # type: ignore[import]
        from cryptography.hazmat.primitives.serialization import Encoding  # noqa: F401

        cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"))
        not_after: datetime = cert.not_valid_after_utc  # type: ignore[attr-defined]
        now = datetime.now(timezone.utc)
        remaining_s = (not_after - now).total_seconds()
        logger.debug(
            "Certificate expiry check: remaining=%.0fs threshold=%ds",
            remaining_s,
            renew_before_expiry_s,
        )
        return remaining_s < renew_before_expiry_s
