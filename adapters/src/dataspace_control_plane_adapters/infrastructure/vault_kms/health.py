"""Vault health probe.

Implements _shared/health.py HealthProbe by calling GET /v1/sys/health.

Vault /sys/health response codes:
  200 — initialised, unsealed, active
  429 — unsealed standby (healthy replica; read-only)
  472 — DR secondary mode (not an error for most use cases)
  473 — performance standby
  501 — not initialised (down)
  503 — sealed (down — operator must intervene)
"""
from __future__ import annotations

import logging

import httpx

from dataspace_control_plane_adapters._shared.health import HealthProbe, HealthReport, HealthStatus

from .config import VaultSettings
from .errors import VaultSealedError

logger = logging.getLogger(__name__)

# HTTP status codes considered operationally healthy for the control plane.
_HEALTHY_STATUS_CODES = {200, 429, 472, 473}


class VaultHealthProbe:
    """Health probe for the Vault KMS infrastructure adapter.

    # implements _shared/health.py HealthProbe

    Calls GET /v1/sys/health without authentication (the endpoint is always
    accessible, even on sealed Vault instances).
    """

    _ADAPTER_NAME = "vault_kms"

    def __init__(self, cfg: VaultSettings) -> None:
        self._cfg = cfg
        self._base_url = str(cfg.vault_addr).rstrip("/")

    async def check(self) -> HealthReport:
        """Probe Vault /sys/health and return a HealthReport.

        Returns:
            HealthReport with:
            - OK       — Vault is active (200), standby (429), or DR/perf standby (472/473).
            - DEGRADED — Vault is reachable but in an unexpected state (e.g. 501).
            - DOWN     — Vault is sealed (503) or unreachable.
        """
        url = f"{self._base_url}/v1/sys/health"
        try:
            async with httpx.AsyncClient(
                timeout=self._cfg.request_timeout_s,
                verify=self._cfg.tls_verify,
            ) as client:
                resp = await client.get(url)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("Vault health check failed: %s", exc)
            return HealthReport(
                adapter=self._ADAPTER_NAME,
                status=HealthStatus.DOWN,
                message=f"Vault unreachable: {exc}",
                details={"url": url},
            )

        code = resp.status_code
        if code in _HEALTHY_STATUS_CODES:
            mode = {200: "active", 429: "standby", 472: "dr_secondary", 473: "perf_standby"}.get(
                code, "unknown"
            )
            return HealthReport(
                adapter=self._ADAPTER_NAME,
                status=HealthStatus.OK,
                message=f"Vault healthy (mode={mode})",
                details={"http_status": code, "mode": mode, "url": url},
            )
        if code == 503:
            return HealthReport(
                adapter=self._ADAPTER_NAME,
                status=HealthStatus.DOWN,
                message="Vault is sealed — operator intervention required.",
                details={"http_status": code, "url": url},
            )
        return HealthReport(
            adapter=self._ADAPTER_NAME,
            status=HealthStatus.DEGRADED,
            message=f"Vault returned unexpected status {code}",
            details={"http_status": code, "url": url},
        )

    def capability_descriptor(self) -> dict:
        """Return a dict describing adapter identity, version, and capabilities."""
        return {
            "adapter": self._ADAPTER_NAME,
            "version": "0.1.0",
            "capabilities": [
                "transit.sign",
                "transit.verify",
                "transit.hmac",
                "pki.issue",
                "pki.revoke",
                "pki.tidy",
            ],
            "vault_addr": str(self._cfg.vault_addr),
            "transit_mount": self._cfg.transit_mount,
            "pki_mount": self._cfg.pki_mount,
        }
