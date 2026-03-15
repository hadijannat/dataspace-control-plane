"""BaSyx adapter health probe.

Checks connectivity and readiness of the three BaSyx services:
- AAS Registry
- Submodel Registry
- Submodel Repository

Each service is probed via either its Spring Boot Actuator ``/actuator/health``
endpoint (if available) or a lightweight list call (``?limit=1``).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from ..._shared.health import HealthProbe, HealthReport, HealthStatus
from .config import BasYxSettings

logger = logging.getLogger(__name__)

_PROBE_TIMEOUT = 5.0
_ACTUATOR_PATH = "/actuator/health"
_AAS_FALLBACK_PATH = "/api/v3.0/shell-descriptors?limit=1"
_SM_REG_FALLBACK_PATH = "/api/v3.0/submodel-descriptors?limit=1"
_SM_REPO_FALLBACK_PATH = "/api/v3.0/submodels?limit=1"


class BasYxHealthProbe:
    """Health probe for all three BaSyx services.

    Implements the HealthProbe protocol from _shared/health.py.
    """

    def __init__(self, cfg: BasYxSettings) -> None:
        self._cfg = cfg

    async def check(self) -> HealthReport:
        """Check connectivity to all BaSyx services.

        Returns:
            HealthReport with status OK, DEGRADED, or DOWN. Individual service
            results are reported in ``details``.
        """
        services = {
            "aas_registry": (
                str(self._cfg.aas_registry_url).rstrip("/"),
                _AAS_FALLBACK_PATH,
            ),
            "submodel_registry": (
                str(self._cfg.submodel_registry_url).rstrip("/"),
                _SM_REG_FALLBACK_PATH,
            ),
            "submodel_repository": (
                str(self._cfg.submodel_repository_url).rstrip("/"),
                _SM_REPO_FALLBACK_PATH,
            ),
        }

        results: dict[str, Any] = {}
        statuses: list[bool] = []

        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT) as client:
            for svc_name, (base_url, fallback_path) in services.items():
                ok, detail = await _probe_service(client, base_url, fallback_path)
                results[svc_name] = {"reachable": ok, "detail": detail}
                statuses.append(ok)

        all_ok = all(statuses)
        any_ok = any(statuses)

        if all_ok:
            status = HealthStatus.OK
            message = "All BaSyx services reachable"
        elif any_ok:
            status = HealthStatus.DEGRADED
            message = "Some BaSyx services unreachable"
        else:
            status = HealthStatus.DOWN
            message = "All BaSyx services unreachable"

        return HealthReport(
            adapter="basyx",
            status=status,
            message=message,
            details=results,
        )

    def capability_descriptor(self) -> dict[str, Any]:
        """Return adapter identity and capability list."""
        return {
            "adapter": "basyx",
            "version": "3.0",
            "capabilities": [
                "aas-registry",
                "submodel-registry",
                "submodel-repository",
            ],
        }


async def _probe_service(
    client: httpx.AsyncClient, base_url: str, fallback_path: str
) -> tuple[bool, str]:
    """Attempt to reach a BaSyx service via actuator/health or a fallback endpoint."""
    # Try Spring Boot Actuator first.
    for path in (_ACTUATOR_PATH, fallback_path):
        try:
            resp = await client.get(f"{base_url}{path}")
            if resp.is_success or resp.status_code in (200, 400, 404):
                # Any HTTP response (even 4xx) means the service is up.
                return True, f"HTTP {resp.status_code} on {path}"
        except (httpx.ConnectError, httpx.TimeoutException):
            continue
    return False, "connection refused or timeout"
