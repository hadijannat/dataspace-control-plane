"""EDC adapter health probe.

Implements the ``HealthProbe`` protocol from ``_shared/health.py``.

Strategy: perform a lightweight Management API call (``GET /v2/assets`` with
``limit=1``) to confirm EDC is reachable and the API key is accepted.
Treats an empty result as healthy — absence of assets does not mean EDC is
down.
"""
from __future__ import annotations

import logging

from ..._shared.errors import AdapterAuthError, AdapterUnavailableError, AdapterTimeoutError
from ..._shared.health import HealthProbe, HealthReport, HealthStatus
from .management_client import EdcManagementClient

logger = logging.getLogger(__name__)

_CAPABILITIES = ["catalog", "negotiation", "transfer", "asset", "policy"]


class EdcHealthProbe:
    """Health probe for the EDC Management API adapter.

    Implements ``HealthProbe`` from ``_shared/health.py``.
    """

    def __init__(self, management_client: EdcManagementClient) -> None:
        self._client = management_client

    async def check(self) -> HealthReport:
        """Probe EDC readiness by listing assets with ``limit=1``.

        Returns:
            ``HealthReport`` with status OK, DEGRADED, or DOWN.
        """
        try:
            await self._client.get("/v2/assets?limit=1")
            return HealthReport(
                adapter="edc",
                status=HealthStatus.OK,
                message="EDC Management API reachable",
            )
        except AdapterAuthError as exc:
            logger.warning("EDC health check auth failure: %s", exc)
            return HealthReport(
                adapter="edc",
                status=HealthStatus.DOWN,
                message=f"EDC API key rejected: {exc}",
            )
        except AdapterTimeoutError as exc:
            logger.warning("EDC health check timed out: %s", exc)
            return HealthReport(
                adapter="edc",
                status=HealthStatus.DEGRADED,
                message=f"EDC Management API timeout: {exc}",
            )
        except AdapterUnavailableError as exc:
            logger.warning("EDC health check unavailable: %s", exc)
            return HealthReport(
                adapter="edc",
                status=HealthStatus.DOWN,
                message=f"EDC Management API unreachable: {exc}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("EDC health check unexpected error")
            return HealthReport(
                adapter="edc",
                status=HealthStatus.DOWN,
                message=f"EDC health check failed: {exc}",
            )

    def capability_descriptor(self) -> dict:
        """Return the capability descriptor for this adapter.

        Returns:
            Dict describing the adapter's identity and supported capabilities.
        """
        return {
            "adapter": "edc",
            "protocol": "EDC-Management-API",
            "version": "0.7+",
            "capabilities": _CAPABILITIES,
        }


# Satisfy the Protocol at import time via structural subtyping check.
_: HealthProbe = EdcHealthProbe.__new__(EdcHealthProbe)  # type: ignore[type-abstract]
