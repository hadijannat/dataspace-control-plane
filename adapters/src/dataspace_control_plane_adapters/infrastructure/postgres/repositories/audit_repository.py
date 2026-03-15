"""PostgreSQL implementation of the audit ports.

Satisfies
---------
- ``core/audit/ports.py :: AuditSinkPort``  — via ``PostgresAuditSink``
- ``core/audit/ports.py :: AuditQueryPort`` — via ``PostgresAuditQuery``

Design invariants
-----------------
- The ``audit_records`` table is **append-only**: no UPDATE or DELETE is ever
  issued against it.  Any such operation is a policy violation.
- Every write and read sets the tenant context via ``set_tenant_context`` so
  that RLS enforces the tenant boundary.
- Aggregates (actors, correlations) are serialized as JSONB blobs.  No ORM
  column mapping into domain fields — we do not want the schema to leak domain
  model internals.
- ``dataclasses.asdict`` is used for actor/correlation serialization because
  the domain types are plain frozen dataclasses.
"""
from __future__ import annotations

import dataclasses
import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from dataspace_control_plane_adapters._shared.errors import AdapterNotFoundError
from dataspace_control_plane_adapters.infrastructure.postgres.errors import (
    PostgresRecordNotFound,
)
from dataspace_control_plane_adapters.infrastructure.postgres.pool import AsyncPgPool
from dataspace_control_plane_adapters.infrastructure.postgres.tenancy import (
    set_tenant_context,
)

logger = logging.getLogger(__name__)


class PostgresAuditSink:
    """Append-only audit sink backed by the ``audit_records`` table.

    Implements ``core/audit/ports.py :: AuditSinkPort``.

    Every ``emit`` call inserts one row.  The operation is idempotent on
    ``record_id`` (PRIMARY KEY) — duplicate emits are silently ignored via
    ``ON CONFLICT DO NOTHING`` to tolerate Temporal retry semantics.
    """

    def __init__(self, pool: AsyncPgPool) -> None:
        self._pool = pool

    async def emit(self, record: Any) -> None:  # record: AuditRecord
        """Insert a single audit record into the append-only table.

        Parameters
        ----------
        record:
            An ``AuditRecord`` instance from ``core/audit/record.py``.
        """
        # Serialize nested value objects as JSON for JSONB columns.
        actor_json = json.dumps(dataclasses.asdict(record.actor))
        correlation_json = json.dumps(_correlation_to_dict(record.correlation))
        payload_json = json.dumps(record.detail) if record.detail else None

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Set tenant context so RLS applies even for writes.
                await set_tenant_context(conn, str(record.tenant_id))
                await conn.execute(
                    """
                    INSERT INTO audit_records
                        (id, tenant_id, category, action, outcome,
                         actor_json, correlation_json, payload_json,
                         retention_class, created_at)
                    VALUES ($1, $2, $3, $4, $5,
                            $6::jsonb, $7::jsonb, $8::jsonb,
                            $9, $10)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    record.record_id,
                    str(record.tenant_id),
                    record.category.value,
                    record.action,
                    record.outcome.value,
                    actor_json,
                    correlation_json,
                    payload_json,
                    record.retention_class.value,
                    record.occurred_at,
                )
        logger.debug(
            "audit emit: record_id=%s tenant=%s action=%s",
            record.record_id,
            record.tenant_id,
            record.action,
        )


class PostgresAuditQuery:
    """Read-only audit query backed by the ``audit_records`` table.

    Implements ``core/audit/ports.py :: AuditQueryPort``.

    Queries always set tenant context before executing so that RLS restricts
    results to the caller's tenant.
    """

    def __init__(self, pool: AsyncPgPool) -> None:
        self._pool = pool

    async def list_records(
        self,
        tenant_id: Any,  # TenantId
        category: Any | None,  # AuditCategory | None
        from_dt: datetime,
        to_dt: datetime,
        limit: int = 100,
    ) -> list[Any]:  # list[AuditRecord]
        """Return audit records within the given time range and optional category."""
        # Lazy core imports — keep adapter import cost low.
        from dataspace_control_plane_core.audit.record import AuditRecord  # noqa: PLC0415

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, str(tenant_id))

                if category is not None:
                    rows = await conn.fetch(
                        """
                        SELECT id, tenant_id, category, action, outcome,
                               actor_json, correlation_json, payload_json,
                               retention_class, created_at
                        FROM audit_records
                        WHERE tenant_id = $1
                          AND category = $2
                          AND created_at BETWEEN $3 AND $4
                        ORDER BY created_at DESC
                        LIMIT $5
                        """,
                        str(tenant_id),
                        category.value,
                        from_dt,
                        to_dt,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id, tenant_id, category, action, outcome,
                               actor_json, correlation_json, payload_json,
                               retention_class, created_at
                        FROM audit_records
                        WHERE tenant_id = $1
                          AND created_at BETWEEN $2 AND $3
                        ORDER BY created_at DESC
                        LIMIT $4
                        """,
                        str(tenant_id),
                        from_dt,
                        to_dt,
                        limit,
                    )

        return [_row_to_audit_record(dict(r)) for r in rows]

    async def get_record(
        self, tenant_id: Any, record_id: str
    ) -> Any:  # AuditRecord
        """Return a single audit record by id, scoped to the tenant."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, str(tenant_id))
                row = await conn.fetchrow(
                    """
                    SELECT id, tenant_id, category, action, outcome,
                           actor_json, correlation_json, payload_json,
                           retention_class, created_at
                    FROM audit_records
                    WHERE tenant_id = $1 AND id = $2
                    """,
                    str(tenant_id),
                    record_id,
                )

        if row is None:
            raise PostgresRecordNotFound("audit_records", record_id)

        return _row_to_audit_record(dict(row))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _correlation_to_dict(correlation: Any) -> dict:
    """Serialize CorrelationContext to a plain dict for JSON storage."""
    return {
        "correlation_id": str(correlation.correlation_id),
        "causation_id": str(correlation.causation_id) if correlation.causation_id else None,
        "workflow_id": correlation.workflow_id,
        "request_id": correlation.request_id,
    }


def _row_to_audit_record(row: dict) -> Any:  # AuditRecord
    """Reconstruct an AuditRecord from a raw database row dict."""
    from dataspace_control_plane_core.audit.record import (  # noqa: PLC0415
        AuditRecord,
        AuditCategory,
        AuditOutcome,
    )
    from dataspace_control_plane_core.domains._shared.actor import (  # noqa: PLC0415
        ActorRef,
        ActorType,
    )
    from dataspace_control_plane_core.domains._shared.correlation import (  # noqa: PLC0415
        CorrelationContext,
    )
    from dataspace_control_plane_core.domains._shared.ids import TenantId  # noqa: PLC0415
    from dataspace_control_plane_core.canonical_models.enums import RetentionClass  # noqa: PLC0415

    # actor_json may be returned as a dict (asyncpg parses JSONB) or str.
    actor_data: dict = _ensure_dict(row["actor_json"])
    correlation_data: dict = _ensure_dict(row["correlation_json"] or {})
    detail: dict = _ensure_dict(row["payload_json"] or {})

    actor = ActorRef(
        subject=actor_data.get("subject", ""),
        actor_type=ActorType(actor_data.get("actor_type", "system")),
        tenant_id=actor_data.get("tenant_id"),
        display_name=actor_data.get("display_name"),
    )

    corr_id_raw = correlation_data.get("correlation_id")
    causation_raw = correlation_data.get("causation_id")
    import uuid as _uuid  # noqa: PLC0415

    correlation = CorrelationContext(
        correlation_id=_uuid.UUID(corr_id_raw) if corr_id_raw else _uuid.uuid4(),
        causation_id=_uuid.UUID(causation_raw) if causation_raw else None,
        workflow_id=correlation_data.get("workflow_id"),
        request_id=correlation_data.get("request_id"),
    )

    return AuditRecord(
        record_id=row["id"],
        tenant_id=TenantId(row["tenant_id"]),
        occurred_at=row["created_at"],
        category=AuditCategory(row["category"]),
        action=row["action"],
        outcome=AuditOutcome(row["outcome"]),
        actor=actor,
        correlation=correlation,
        detail=detail,
        retention_class=RetentionClass(row["retention_class"]),
    )


def _ensure_dict(value: Any) -> dict:
    """Return value as dict — asyncpg may return JSONB as dict or str."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return {}
