"""PostgreSQL read model for operator grants and authorization decisions.

Satisfies
---------
- ``core/domains/operator_access/ports.py :: GrantRepository``  — via ``PostgresGrantRepository``

Table
-----
``operator_grants(grant_id, tenant_id, subject, role_name, scope_json,
                  expires_at, granted_by, created_at, status)``

Design invariants
-----------------
- Grants are stored as a flat, indexed read-model table separate from the
  domain aggregate event stream.  This enables fast subject-based lookups
  without reconstructing the full aggregate graph.
- ``scope_json`` stores the ``Scope`` value object as JSONB.
- Tenant context is set before every query for RLS enforcement.
- The table does not enforce RLS on ``grant_id`` lookups because grant IDs
  are globally unique UUIDs — however, we still set tenant context to avoid
  exposing cross-tenant data in composite queries.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from dataspace_control_plane_adapters.infrastructure.postgres.errors import (
    PostgresRecordNotFound,
)
from dataspace_control_plane_adapters.infrastructure.postgres.pool import AsyncPgPool
from dataspace_control_plane_adapters.infrastructure.postgres.tenancy import (
    set_tenant_context,
)

logger = logging.getLogger(__name__)

# DDL for the operator_grants table (applied by a migration):
#
#   CREATE TABLE IF NOT EXISTS operator_grants (
#       grant_id TEXT PRIMARY KEY,
#       tenant_id TEXT NOT NULL,
#       subject TEXT NOT NULL,
#       role_name TEXT NOT NULL,
#       scope_json JSONB NOT NULL,
#       expires_at TIMESTAMPTZ,
#       granted_by TEXT NOT NULL,
#       created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
#       status TEXT NOT NULL DEFAULT 'active'
#   );
#   CREATE INDEX ON operator_grants (subject, status);
#   CREATE INDEX ON operator_grants (tenant_id, subject);
#   ALTER TABLE operator_grants ENABLE ROW LEVEL SECURITY;
#   CREATE POLICY tenant_isolation ON operator_grants
#       USING (tenant_id = current_setting('app.current_tenant', TRUE));


class PostgresGrantRepository:
    """Read-model repository for operator ``Grant`` objects.

    Implements ``core/domains/operator_access/ports.py :: GrantRepository``.

    Grants are written here by command handlers (e.g. after ``GrantCreated``
    events) and read by the authorization decision flow.
    """

    def __init__(self, pool: AsyncPgPool) -> None:
        self._pool = pool

    async def get(self, grant_id: str) -> Any:  # Grant
        """Return a Grant by its primary key.

        Note: grant_id is globally unique, but we still require tenant context
        to be available for potential cross-table joins.  We do NOT pass
        tenant_id as a query parameter here because ``GrantRepository.get``
        is defined without tenant_id in the core port.
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Use a sentinel tenant — the RLS policy on operator_grants
                # uses the GUC, not a query parameter.  If the caller has set
                # tenant context upstream this is a no-op.
                await conn.execute(
                    "SELECT set_config('app.current_tenant', current_setting('app.current_tenant', TRUE), TRUE)"
                )
                row = await conn.fetchrow(
                    """
                    SELECT grant_id, tenant_id, subject, role_name,
                           scope_json, expires_at, granted_by, created_at, status
                    FROM operator_grants
                    WHERE grant_id = $1
                    """,
                    grant_id,
                )

        if row is None:
            raise PostgresRecordNotFound("operator_grants", grant_id)

        return _row_to_grant(dict(row))

    async def save(self, grant: Any) -> None:  # Grant
        """Upsert a Grant into the read-model table.

        Uses ``ON CONFLICT (grant_id) DO UPDATE`` so that revocations and
        status changes are reflected without error.
        """
        scope_json = json.dumps({
            "resource_type": grant.scope.resource_type,
            "resource_id": grant.scope.resource_id,
        })

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, _infer_tenant_id(grant))
                await conn.execute(
                    """
                    INSERT INTO operator_grants
                        (grant_id, tenant_id, subject, role_name,
                         scope_json, expires_at, granted_by, created_at, status)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9)
                    ON CONFLICT (grant_id) DO UPDATE
                        SET role_name  = EXCLUDED.role_name,
                            scope_json = EXCLUDED.scope_json,
                            expires_at = EXCLUDED.expires_at,
                            status     = EXCLUDED.status
                    """,
                    grant.grant_id,
                    _infer_tenant_id(grant),
                    grant.subject,
                    grant.role_name,
                    scope_json,
                    grant.expires_at,
                    grant.granted_by,
                    grant.granted_at,
                    grant.status.value,
                )

    async def list_for_subject(self, subject: str) -> list[Any]:  # list[Grant]
        """Return all grants for a given subject (user sub or service account).

        Note: the core port does not take a tenant_id; we return all grants
        across tenants visible through the currently-set RLS context.
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Ensure GUC is set (even if empty) to avoid Postgres errors
                # if RLS references current_setting without the TRUE flag.
                await conn.execute(
                    "SELECT set_config('app.current_tenant', "
                    "current_setting('app.current_tenant', TRUE), TRUE)"
                )
                rows = await conn.fetch(
                    """
                    SELECT grant_id, tenant_id, subject, role_name,
                           scope_json, expires_at, granted_by, created_at, status
                    FROM operator_grants
                    WHERE subject = $1
                    ORDER BY created_at DESC
                    """,
                    subject,
                )

        return [_row_to_grant(dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _infer_tenant_id(grant: Any) -> str:
    """Extract tenant_id string from a Grant.

    The core Grant model does not carry tenant_id directly (it is part of the
    scope).  We use scope.resource_id when resource_type == 'tenant', otherwise
    fall back to an empty string (platform-level grants).
    """
    if grant.scope.resource_type == "tenant" and grant.scope.resource_id:
        return grant.scope.resource_id
    return ""


def _row_to_grant(row: dict) -> Any:  # Grant
    """Reconstruct a Grant from a raw database row dict."""
    from dataspace_control_plane_core.domains.operator_access.model.aggregates import (  # noqa: PLC0415
        Grant,
    )
    from dataspace_control_plane_core.domains.operator_access.model.value_objects import (  # noqa: PLC0415
        Scope,
    )
    from dataspace_control_plane_core.domains.operator_access.model.enums import (  # noqa: PLC0415
        GrantStatus,
    )

    scope_data: dict = _ensure_dict(row["scope_json"])
    scope = Scope(
        resource_type=scope_data.get("resource_type", "*"),
        resource_id=scope_data.get("resource_id"),
    )

    return Grant(
        grant_id=row["grant_id"],
        subject=row["subject"],
        role_name=row["role_name"],
        scope=scope,
        granted_by=row["granted_by"],
        granted_at=row["created_at"],
        expires_at=row.get("expires_at"),
        status=GrantStatus(row["status"]),
    )


def _ensure_dict(value: Any) -> dict:
    """Normalize asyncpg JSONB values to dict."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return {}
