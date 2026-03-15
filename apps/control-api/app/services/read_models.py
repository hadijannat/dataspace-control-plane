"""
Read-model façade for queryable projections.

This module is NOT the source of truth for any entity. It exposes queryable
projections backed by asyncpg for list pages and dashboards. The pool is
injected from lifespan state.

All queries use asyncpg positional parameter style ($1, $2, …).
Tables are expected to exist once the schema migration is applied; until then
these queries will raise asyncpg errors which callers should handle gracefully.
"""
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Procedure read-model queries
# ---------------------------------------------------------------------------


async def list_procedures(
    pool: Any,
    tenant_id: str,
    status: str | None,
    limit: int,
    offset: int,
) -> list[dict]:
    """
    Return a paginated list of procedure records for a given tenant.

    Parameters
    ----------
    pool:
        An asyncpg ``Pool`` (injected from lifespan state).
    tenant_id:
        Tenant scope filter — always required to enforce tenancy boundaries.
    status:
        Optional status filter (e.g. ``"RUNNING"``, ``"COMPLETED"``). When
        ``None``, all statuses are returned.
    limit:
        Maximum number of rows to return (asyncpg ``$3``).
    offset:
        Number of rows to skip for pagination (asyncpg ``$4``).

    Returns
    -------
    list[dict]
        Each item is a dict derived from an asyncpg ``Record``.
    """
    async with pool.acquire() as conn:
        if status is not None:
            rows = await conn.fetch(
                """
                SELECT workflow_id, procedure_type, tenant_id, status,
                       result, failure_message, search_attributes,
                       started_at, updated_at
                FROM   procedures
                WHERE  1=1
                  AND  tenant_id = $1
                  AND  status    = $2
                ORDER  BY started_at DESC
                LIMIT  $3
                OFFSET $4
                """,
                tenant_id,
                status,
                limit,
                offset,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT workflow_id, procedure_type, tenant_id, status,
                       result, failure_message, search_attributes,
                       started_at, updated_at
                FROM   procedures
                WHERE  1=1
                  AND  tenant_id = $1
                ORDER  BY started_at DESC
                LIMIT  $2
                OFFSET $3
                """,
                tenant_id,
                limit,
                offset,
            )
    return [dict(r) for r in rows]


async def count_procedures(
    pool: Any,
    tenant_id: str,
    status: str | None,
) -> int:
    async with pool.acquire() as conn:
        if status is not None:
            return int(
                await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM   procedures
                    WHERE  tenant_id = $1
                      AND  status    = $2
                    """,
                    tenant_id,
                    status,
                )
            )
        return int(
            await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM   procedures
                WHERE  tenant_id = $1
                """,
                tenant_id,
            )
        )


async def get_procedure(pool: Any, workflow_id: str) -> dict | None:
    """
    Fetch a single procedure record by its workflow_id.

    Parameters
    ----------
    pool:
        An asyncpg ``Pool``.
    workflow_id:
        Temporal workflow identifier (unique across tenants).

    Returns
    -------
    dict or None
        The procedure record as a dict, or ``None`` if not found.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT workflow_id, procedure_type, tenant_id, status,
                   result, failure_message, search_attributes,
                   started_at, updated_at
            FROM   procedures
            WHERE  1=1
              AND  workflow_id = $1
            """,
            workflow_id,
        )
    if row is None:
        return None
    return dict(row)


# ---------------------------------------------------------------------------
# Tenant read-model queries
# ---------------------------------------------------------------------------


async def list_tenants(
    pool: Any,
    limit: int,
    offset: int,
    tenant_ids: list[str] | None = None,
) -> list[dict]:
    """
    Return a paginated list of tenant records.

    Parameters
    ----------
    pool:
        An asyncpg ``Pool``.
    limit:
        Maximum number of rows to return.
    offset:
        Number of rows to skip.

    Returns
    -------
    list[dict]
        Each item is a dict derived from an asyncpg ``Record``.
    """
    async with pool.acquire() as conn:
        if tenant_ids:
            rows = await conn.fetch(
                """
                SELECT tenant_id, display_name, status, legal_entity_id,
                       created_at, updated_at
                FROM   tenants
                WHERE  tenant_id = ANY($1::text[])
                ORDER  BY created_at DESC
                LIMIT  $2
                OFFSET $3
                """,
                tenant_ids,
                limit,
                offset,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT tenant_id, display_name, status, legal_entity_id,
                       created_at, updated_at
                FROM   tenants
                ORDER  BY created_at DESC
                LIMIT  $1
                OFFSET $2
                """,
                limit,
                offset,
            )
    return [dict(r) for r in rows]


async def count_tenants(pool: Any, tenant_ids: list[str] | None = None) -> int:
    async with pool.acquire() as conn:
        if tenant_ids:
            return int(
                await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM   tenants
                    WHERE  tenant_id = ANY($1::text[])
                    """,
                    tenant_ids,
                )
            )
        return int(await conn.fetchval("SELECT COUNT(*) FROM tenants"))


async def get_tenant(pool: Any, tenant_id: str) -> dict | None:
    """
    Fetch a single tenant record by its tenant_id.

    Parameters
    ----------
    pool:
        An asyncpg ``Pool``.
    tenant_id:
        Logical tenant identifier.

    Returns
    -------
    dict or None
        The tenant record as a dict, or ``None`` if not found.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT tenant_id, display_name, status, legal_entity_id,
                   created_at, updated_at
            FROM   tenants
            WHERE  1=1
              AND  tenant_id = $1
            """,
            tenant_id,
        )
    if row is None:
        return None
    return dict(row)
