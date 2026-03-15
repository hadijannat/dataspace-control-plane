"""Tenant isolation enforcement for the Postgres adapter.

PostgreSQL Row-Level Security (RLS) is the hard tenant boundary. Every query
against a multi-tenant table MUST be preceded by ``set_tenant_context`` so
that RLS policies based on ``current_setting('app.current_tenant', TRUE)``
apply correctly.

Migration SQL snippets are provided as string constants here so that migration
scripts can apply them uniformly across all tenant-scoped tables.

Design decisions
----------------
- We use ``SET LOCAL`` so the GUC is scoped to the current transaction.  This
  is safer than ``SET`` (session-level) because pooled connections are reused
  and a previous caller's context must not bleed into the next request.
- ``legal_entity_id`` is optional; not all queries narrow to a single legal
  entity, but when they do we set ``app.current_legal_entity`` as well.
- We intentionally do NOT catch asyncpg errors here — the caller's repository
  is responsible for mapping database errors to adapter errors.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# RLS policy SQL template (applied during migrations)
# ---------------------------------------------------------------------------

TENANT_RLS_POLICY = """
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON {table}
    USING (tenant_id = current_setting('app.current_tenant', TRUE));
"""
"""SQL template for tenant RLS policies.

Usage in a migration::

    TENANT_RLS_POLICY.format(table="negotiations")

The ``TRUE`` flag on ``current_setting`` makes Postgres return an empty string
instead of raising an error when the GUC is not set (e.g. during superuser
maintenance queries).
"""


# ---------------------------------------------------------------------------
# Runtime enforcement
# ---------------------------------------------------------------------------


async def set_tenant_context(
    conn: Any,
    tenant_id: str,
    legal_entity_id: str | None = None,
) -> None:
    """Set session-local GUCs that drive RLS policies.

    Must be called inside a transaction (``SET LOCAL`` is transaction-scoped).
    Call this immediately after acquiring a connection and before any DML.

    Parameters
    ----------
    conn:
        An asyncpg connection obtained from ``AsyncPgPool.acquire()``.
    tenant_id:
        The platform tenant identifier.  RLS policies check this value against
        the ``tenant_id`` column on all multi-tenant tables.
    legal_entity_id:
        Optional additional scoping.  When set, ``app.current_legal_entity``
        is available for application-level filtering (not currently enforced by
        RLS, but useful for query optimisation hints and audit).
    """
    # SET LOCAL is transaction-scoped; safe on pooled connections.
    await conn.execute("SET LOCAL app.current_tenant = $1", tenant_id)
    if legal_entity_id is not None:
        await conn.execute("SET LOCAL app.current_legal_entity = $1", legal_entity_id)


async def assert_tenant_context(conn: Any) -> str:
    """Read back the active tenant GUC from the connection.

    Returns the tenant_id string, or raises ``PostgresTenancyViolation`` if
    the context has not been set.  Used in integration tests and repository
    pre-condition checks.
    """
    from .errors import PostgresTenancyViolation  # local import to avoid cycles

    row = await conn.fetchrow(
        "SELECT current_setting('app.current_tenant', TRUE) AS tenant_id"
    )
    tenant_id: str = row["tenant_id"] if row else ""
    if not tenant_id:
        raise PostgresTenancyViolation(
            "app.current_tenant GUC is not set; call set_tenant_context() before querying"
        )
    return tenant_id
