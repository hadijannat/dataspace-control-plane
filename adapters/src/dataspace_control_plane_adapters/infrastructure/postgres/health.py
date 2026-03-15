"""Health probe for the PostgreSQL adapter.

Implements ``_shared/health.py :: HealthProbe``.

The probe issues a lightweight ``SELECT 1`` query with a 1-second timeout.
If the query succeeds the pool is healthy.  Connection failures, timeouts,
or pool exhaustion are reported as DOWN.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)
from dataspace_control_plane_adapters.infrastructure.postgres.pool import AsyncPgPool

logger = logging.getLogger(__name__)

_PROBE_TIMEOUT_S = 1.0
"""Maximum time the health check query is allowed to run."""


class PostgresHealthProbe:
    """Health probe for a PostgreSQL connection pool.

    Satisfies ``_shared/health.py :: HealthProbe`` (structural subtyping via Protocol).

    Checks::
        SELECT 1  -- lightweight roundtrip; confirms pool is live and responsive.

    Result::
        HealthStatus.OK      — SELECT succeeded within timeout
        HealthStatus.DOWN    — connection refused, timeout, or pool closed
    """

    def __init__(self, pool: AsyncPgPool, adapter_name: str = "postgres") -> None:
        self._pool = pool
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        """Execute a lightweight query and return a HealthReport."""
        try:
            async with asyncio.timeout(_PROBE_TIMEOUT_S):
                async with self._pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT 1 AS ok")
                    assert row is not None and row["ok"] == 1
        except asyncio.TimeoutError:
            logger.warning("postgres health probe timed out after %.1fs", _PROBE_TIMEOUT_S)
            return HealthReport(
                adapter=self._adapter_name,
                status=HealthStatus.DOWN,
                message=f"Health check query timed out after {_PROBE_TIMEOUT_S}s",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("postgres health probe failed: %s", exc)
            return HealthReport(
                adapter=self._adapter_name,
                status=HealthStatus.DOWN,
                message=f"Connection error: {exc}",
            )

        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="SELECT 1 succeeded",
        )

    def capability_descriptor(self) -> dict:
        """Return adapter identity and capability metadata."""
        return {
            "adapter": self._adapter_name,
            "type": "postgres",
            "capabilities": [
                "audit_sink",
                "audit_query",
                "negotiation_repository",
                "entitlement_repository",
                "grant_repository",
                "transactional_outbox",
            ],
            "version": "0.1.0",
            "rls_enabled": True,
        }
