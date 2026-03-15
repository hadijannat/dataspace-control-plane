"""Factory that wires Postgres implementations to core ports.

Usage (at container startup)::

    from dataspace_control_plane_adapters.infrastructure.postgres.api import (
        AsyncPgPool,
        PostgresPoolSettings,
        make_postgres_ports,
    )

    settings = PostgresPoolSettings()
    async with AsyncPgPool(settings) as pool:
        ports = make_postgres_ports(pool)
        # pass ports["audit_sink"], ports["negotiation_repo"], etc. to services

The returned dict uses stable string keys that match the injection names
expected by ``apps/control-api`` and ``apps/temporal-workers``.
"""
from __future__ import annotations

from typing import Any

from dataspace_control_plane_adapters.infrastructure.postgres.pool import AsyncPgPool
from dataspace_control_plane_adapters.infrastructure.postgres.repositories.audit_repository import (
    PostgresAuditSink,
    PostgresAuditQuery,
)
from dataspace_control_plane_adapters.infrastructure.postgres.repositories.negotiation_repository import (
    PostgresNegotiationRepository,
    PostgresEntitlementRepository,
)
from dataspace_control_plane_adapters.infrastructure.postgres.read_models.operator_grants import (
    PostgresGrantRepository,
)


def make_postgres_ports(pool: AsyncPgPool) -> dict[str, Any]:
    """Instantiate all Postgres-backed port implementations and return them keyed by port name.

    Parameters
    ----------
    pool:
        An open ``AsyncPgPool`` instance.

    Returns
    -------
    dict with keys:
        ``audit_sink``        → ``PostgresAuditSink``        (AuditSinkPort)
        ``audit_query``       → ``PostgresAuditQuery``       (AuditQueryPort)
        ``negotiation_repo``  → ``PostgresNegotiationRepository`` (NegotiationRepository)
        ``entitlement_repo``  → ``PostgresEntitlementRepository`` (EntitlementRepository)
        ``grant_repo``        → ``PostgresGrantRepository``  (GrantRepository)
    """
    return {
        "audit_sink": PostgresAuditSink(pool),
        "audit_query": PostgresAuditQuery(pool),
        "negotiation_repo": PostgresNegotiationRepository(pool),
        "entitlement_repo": PostgresEntitlementRepository(pool),
        "grant_repo": PostgresGrantRepository(pool),
    }
