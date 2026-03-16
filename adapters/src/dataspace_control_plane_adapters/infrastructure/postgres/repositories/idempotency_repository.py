"""PostgreSQL-backed HTTP idempotency repository."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from dataspace_control_plane_adapters.infrastructure.postgres.pool import AsyncPgPool
from dataspace_control_plane_adapters.infrastructure.postgres.tenancy import (
    set_tenant_context,
)


IdempotencyAcquireOutcome = Literal["acquired", "replay", "conflict"]


@dataclass(frozen=True)
class IdempotencyRecord:
    tenant_id: str
    procedure_type: str
    idempotency_key: str
    request_fingerprint: str
    workflow_id: str
    run_id: str | None
    response_json: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class IdempotencyAcquireResult:
    outcome: IdempotencyAcquireOutcome
    record: IdempotencyRecord


class PostgresIdempotencyRepository:
    """Durable request-idempotency repository scoped by tenant and procedure."""

    def __init__(self, pool: AsyncPgPool) -> None:
        self._pool = pool

    async def acquire(
        self,
        *,
        tenant_id: str,
        procedure_type: str,
        idempotency_key: str,
        request_fingerprint: str,
        workflow_id: str,
        response_json: dict[str, Any],
        status: str,
    ) -> IdempotencyAcquireResult:
        now = datetime.now(timezone.utc)
        response_payload = json.dumps(response_json)

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, tenant_id)
                row = await conn.fetchrow(
                    """
                    INSERT INTO http_idempotency_keys (
                        tenant_id,
                        procedure_type,
                        idempotency_key,
                        request_fingerprint,
                        workflow_id,
                        response_json,
                        status,
                        created_at,
                        updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9)
                    ON CONFLICT (tenant_id, procedure_type, idempotency_key) DO NOTHING
                    RETURNING tenant_id, procedure_type, idempotency_key, request_fingerprint,
                              workflow_id, run_id, response_json, status, created_at, updated_at
                    """,
                    tenant_id,
                    procedure_type,
                    idempotency_key,
                    request_fingerprint,
                    workflow_id,
                    response_payload,
                    status,
                    now,
                    now,
                )
                if row is None:
                    row = await conn.fetchrow(
                        """
                        SELECT tenant_id, procedure_type, idempotency_key, request_fingerprint,
                               workflow_id, run_id, response_json, status, created_at, updated_at
                        FROM http_idempotency_keys
                        WHERE tenant_id = $1
                          AND procedure_type = $2
                          AND idempotency_key = $3
                        """,
                        tenant_id,
                        procedure_type,
                        idempotency_key,
                    )
                    assert row is not None
                    record = _row_to_record(dict(row))
                    if record.request_fingerprint != request_fingerprint:
                        return IdempotencyAcquireResult(outcome="conflict", record=record)
                    return IdempotencyAcquireResult(outcome="replay", record=record)

        return IdempotencyAcquireResult(
            outcome="acquired",
            record=_row_to_record(dict(row)),
        )

    async def finalize(
        self,
        *,
        tenant_id: str,
        procedure_type: str,
        idempotency_key: str,
        run_id: str | None,
        response_json: dict[str, Any],
        status: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, tenant_id)
                await conn.execute(
                    """
                    UPDATE http_idempotency_keys
                    SET run_id = $4,
                        response_json = $5::jsonb,
                        status = $6,
                        updated_at = NOW()
                    WHERE tenant_id = $1
                      AND procedure_type = $2
                      AND idempotency_key = $3
                    """,
                    tenant_id,
                    procedure_type,
                    idempotency_key,
                    run_id,
                    json.dumps(response_json),
                    status,
                )

    async def release(
        self,
        *,
        tenant_id: str,
        procedure_type: str,
        idempotency_key: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, tenant_id)
                await conn.execute(
                    """
                    DELETE FROM http_idempotency_keys
                    WHERE tenant_id = $1
                      AND procedure_type = $2
                      AND idempotency_key = $3
                    """,
                    tenant_id,
                    procedure_type,
                    idempotency_key,
                )


def _row_to_record(row: dict[str, Any]) -> IdempotencyRecord:
    response_json = row["response_json"]
    if isinstance(response_json, str):
        response_json = json.loads(response_json)
    return IdempotencyRecord(
        tenant_id=row["tenant_id"],
        procedure_type=row["procedure_type"],
        idempotency_key=row["idempotency_key"],
        request_fingerprint=row["request_fingerprint"],
        workflow_id=row["workflow_id"],
        run_id=row.get("run_id"),
        response_json=response_json,
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
