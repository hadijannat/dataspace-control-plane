"""Health probe for the Keycloak adapter.

Implements ``_shared/health.py :: HealthProbe``.

The probe fetches the OIDC Discovery document (``/.well-known/openid-configuration``)
for the configured realm.  A 200 response indicates Keycloak is reachable and
the realm exists.  Any non-200 or network error results in DOWN.

This check does not attempt token verification — it is purely a connectivity
and realm-reachability check suitable for Kubernetes readiness probes.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)
from dataspace_control_plane_adapters.infrastructure.keycloak.config import KeycloakSettings

logger = logging.getLogger(__name__)

_PROBE_TIMEOUT_S = 5.0
"""Maximum time the health check request is allowed to run."""


class KeycloakHealthProbe:
    """Health probe for the Keycloak human-IAM adapter.

    Satisfies ``_shared/health.py :: HealthProbe`` (structural subtyping via Protocol).

    Check: GET ``{base_url}/realms/{realm}/.well-known/openid-configuration``

    Result::
        HealthStatus.OK      — HTTP 200 within timeout
        HealthStatus.DOWN    — HTTP non-200, connection refused, or timeout
    """

    def __init__(
        self,
        settings: KeycloakSettings,
        adapter_name: str = "keycloak",
    ) -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        """Probe Keycloak by fetching the OIDC discovery document."""
        url = self._settings.openid_config_uri
        try:
            async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
                resp = await client.get(url)
        except httpx.TimeoutException:
            return HealthReport(
                adapter=self._adapter_name,
                status=HealthStatus.DOWN,
                message=f"OIDC discovery request timed out after {_PROBE_TIMEOUT_S}s",
                details={"url": url},
            )
        except httpx.RequestError as exc:
            return HealthReport(
                adapter=self._adapter_name,
                status=HealthStatus.DOWN,
                message=f"OIDC discovery request failed: {exc}",
                details={"url": url},
            )

        if resp.status_code == 200:
            return HealthReport(
                adapter=self._adapter_name,
                status=HealthStatus.OK,
                message="OIDC discovery endpoint reachable",
                details={"url": url, "status_code": resp.status_code},
            )

        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.DOWN,
            message=f"OIDC discovery returned HTTP {resp.status_code}",
            details={"url": url, "status_code": resp.status_code},
        )

    def capability_descriptor(self) -> dict:
        """Return adapter identity and capability metadata."""
        return {
            "adapter": self._adapter_name,
            "type": "keycloak",
            "capabilities": [
                "oidc_verification",
                "jwks_cache",
                "admin_api",
                "principal_mapping",
                "authorization_decision",
            ],
            "realm": self._settings.realm,
            "base_url": str(self._settings.base_url),
            "version": "0.1.0",
        }
