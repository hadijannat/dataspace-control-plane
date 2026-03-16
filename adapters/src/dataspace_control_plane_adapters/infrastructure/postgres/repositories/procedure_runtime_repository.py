"""PostgreSQL-backed procedure runtime projection repository."""
from __future__ import annotations

import json
from typing import Any

from dataspace_control_plane_adapters.infrastructure.postgres.pool import AsyncPgPool
from dataspace_control_plane_adapters.infrastructure.postgres.tenancy import (
    set_tenant_context,
)


class PostgresProcedureRuntimeRepository:
    """Writes the coarse runtime projection used by control-api fallbacks."""

    def __init__(self, pool: AsyncPgPool) -> None:
        self._pool = pool

    async def upsert_state(
        self,
        *,
        workflow_id: str,
        procedure_type: str,
        tenant_id: str,
        status: str,
        phase: str | None = None,
        progress_percent: int | None = None,
        search_attributes: dict[str, Any],
        links: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        failure_message: str | None = None,
    ) -> None:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, tenant_id)
                await conn.execute(
                    """
                    INSERT INTO procedures (
                        workflow_id,
                        procedure_type,
                        tenant_id,
                        status,
                        phase,
                        progress_percent,
                        result,
                        failure_message,
                        search_attributes,
                        links,
                        started_at,
                        updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9::jsonb, $10::jsonb, NOW(), NOW())
                    ON CONFLICT (workflow_id) DO UPDATE
                    SET status = EXCLUDED.status,
                        phase = EXCLUDED.phase,
                        progress_percent = EXCLUDED.progress_percent,
                        result = EXCLUDED.result,
                        failure_message = EXCLUDED.failure_message,
                        search_attributes = EXCLUDED.search_attributes,
                        links = EXCLUDED.links,
                        updated_at = NOW()
                    """,
                    workflow_id,
                    procedure_type,
                    tenant_id,
                    status,
                    phase,
                    progress_percent,
                    json.dumps(result) if result is not None else None,
                    failure_message,
                    json.dumps(search_attributes),
                    json.dumps(links or {}),
                )
