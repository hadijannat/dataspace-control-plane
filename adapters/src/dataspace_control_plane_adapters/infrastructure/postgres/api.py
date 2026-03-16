"""Public import surface for the PostgreSQL infrastructure adapter.

Other adapters and apps import from here — never from internal sub-modules.

Quick-start::

    from dataspace_control_plane_adapters.infrastructure.postgres.api import (
        AsyncPgPool,
        PostgresPoolSettings,
        make_postgres_ports,
        PostgresHealthProbe,
    )
"""
from __future__ import annotations

from dataspace_control_plane_adapters.infrastructure.postgres.pool import (
    AsyncPgPool,
    PostgresPoolSettings,
)
from dataspace_control_plane_adapters.infrastructure.postgres.ports_impl import (
    make_postgres_ports,
)
from dataspace_control_plane_adapters.infrastructure.postgres.health import (
    PostgresHealthProbe,
)
from dataspace_control_plane_adapters.infrastructure.postgres.errors import (
    PostgresError,
    PostgresTenancyViolation,
    PostgresVersionConflict,
    PostgresRecordNotFound,
)
from dataspace_control_plane_adapters.infrastructure.postgres.tenancy import (
    set_tenant_context,
    assert_tenant_context,
    TENANT_RLS_POLICY,
)
from dataspace_control_plane_adapters.infrastructure.postgres.outbox import (
    OutboxEntry,
    PostgresOutboxWriter,
    PostgresOutboxPoller,
)
from dataspace_control_plane_adapters.infrastructure.postgres.locks import (
    acquire_advisory_lock,
    try_advisory_lock,
    MIGRATION_LOCK_KEY,
    GRANT_PROJECTION_LOCK_KEY,
    AUDIT_ARCHIVAL_LOCK_KEY,
)
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
from dataspace_control_plane_adapters.infrastructure.postgres.repositories.idempotency_repository import (
    IdempotencyAcquireResult,
    IdempotencyRecord,
    PostgresIdempotencyRepository,
)
from dataspace_control_plane_adapters.infrastructure.postgres.repositories.procedure_runtime_repository import (
    PostgresProcedureRuntimeRepository,
)
from dataspace_control_plane_adapters.infrastructure.postgres.schema import (
    PostgresSchemaChecker,
    SchemaReadiness,
)

__all__ = [
    # Pool
    "AsyncPgPool",
    "PostgresPoolSettings",
    # Factory
    "make_postgres_ports",
    # Health
    "PostgresHealthProbe",
    # Errors
    "PostgresError",
    "PostgresTenancyViolation",
    "PostgresVersionConflict",
    "PostgresRecordNotFound",
    # Tenancy
    "set_tenant_context",
    "assert_tenant_context",
    "TENANT_RLS_POLICY",
    # Outbox
    "OutboxEntry",
    "PostgresOutboxWriter",
    "PostgresOutboxPoller",
    # Locks
    "acquire_advisory_lock",
    "try_advisory_lock",
    "MIGRATION_LOCK_KEY",
    "GRANT_PROJECTION_LOCK_KEY",
    "AUDIT_ARCHIVAL_LOCK_KEY",
    # Repositories
    "PostgresAuditSink",
    "PostgresAuditQuery",
    "PostgresNegotiationRepository",
    "PostgresEntitlementRepository",
    "PostgresGrantRepository",
    "IdempotencyRecord",
    "IdempotencyAcquireResult",
    "PostgresIdempotencyRepository",
    "PostgresProcedureRuntimeRepository",
    "PostgresSchemaChecker",
    "SchemaReadiness",
]
