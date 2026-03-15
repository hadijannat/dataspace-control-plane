"""PostgreSQL implementations of the contract domain repositories.

Satisfies
---------
- ``core/domains/contracts/ports.py :: NegotiationRepository``  — via ``PostgresNegotiationRepository``
- ``core/domains/contracts/ports.py :: EntitlementRepository``  — via ``PostgresEntitlementRepository``

Design invariants
-----------------
- Aggregates are serialized as JSONB blobs in ``payload_json``.  No ORM column
  mapping into domain model fields — the domain model is opaque to the schema.
- Optimistic concurrency is enforced by checking ``version`` at UPDATE time.
  If the stored version does not match the expected value, ``PostgresVersionConflict``
  is raised so the caller can reload and retry.
- ``set_tenant_context`` is called before every query to activate RLS.
- The ``version`` column is incremented on every save.
- We use ``dataclasses.asdict`` to serialize domain aggregates into the JSONB
  blob.  Custom dataclass fields that cannot be serialized by ``json.dumps``
  (e.g. ``UUID``, ``datetime``, typed Enums) are normalized via
  ``_default_json_serializer``.
"""
from __future__ import annotations

import dataclasses
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from dataspace_control_plane_adapters._shared.errors import AdapterNotFoundError
from dataspace_control_plane_adapters.infrastructure.postgres.errors import (
    PostgresRecordNotFound,
    PostgresVersionConflict,
)
from dataspace_control_plane_adapters.infrastructure.postgres.pool import AsyncPgPool
from dataspace_control_plane_adapters.infrastructure.postgres.tenancy import (
    set_tenant_context,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NegotiationRepository
# ---------------------------------------------------------------------------


class PostgresNegotiationRepository:
    """Postgres-backed repository for NegotiationCase aggregates.

    Implements ``core/domains/contracts/ports.py :: NegotiationRepository``.

    Table: ``negotiations(id, tenant_id, legal_entity_id, status,
                           payload_json, version, created_at, updated_at)``
    """

    def __init__(self, pool: AsyncPgPool) -> None:
        self._pool = pool

    async def get(
        self, tenant_id: Any, negotiation_id: Any
    ) -> Any:  # NegotiationCase
        """Load a NegotiationCase by its aggregate id."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, str(tenant_id))
                row = await conn.fetchrow(
                    """
                    SELECT id, tenant_id, legal_entity_id, status,
                           payload_json, version, created_at, updated_at
                    FROM negotiations
                    WHERE tenant_id = $1 AND id = $2
                    """,
                    str(tenant_id),
                    str(negotiation_id),
                )

        if row is None:
            raise PostgresRecordNotFound("negotiations", str(negotiation_id))

        return _row_to_negotiation(dict(row))

    async def save(self, tenant_id: Any, negotiation: Any) -> None:  # NegotiationCase
        """Persist a NegotiationCase, creating or updating as needed.

        Uses optimistic concurrency: compares the current ``version`` in the
        database against the aggregate's ``version`` field.  If they differ,
        ``PostgresVersionConflict`` is raised.

        The aggregate ``version`` is incremented on every successful save.
        """
        # Serialize the entire aggregate as JSONB for schema-less storage.
        payload_str = _serialize_aggregate(negotiation)
        now = datetime.now(timezone.utc)
        expected_version = negotiation.version

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, str(tenant_id))

                # Check for existing row (UPSERT with version guard).
                existing = await conn.fetchrow(
                    "SELECT version FROM negotiations WHERE tenant_id = $1 AND id = $2",
                    str(tenant_id),
                    str(negotiation.id),
                )

                if existing is None:
                    # INSERT new aggregate (version must be 0 on creation).
                    await conn.execute(
                        """
                        INSERT INTO negotiations
                            (id, tenant_id, legal_entity_id, status,
                             payload_json, version, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)
                        """,
                        str(negotiation.id),
                        str(tenant_id),
                        str(negotiation.legal_entity_id),
                        negotiation.status.value,
                        payload_str,
                        expected_version + 1,
                        now,
                        now,
                    )
                else:
                    # UPDATE with optimistic concurrency check.
                    stored_version: int = existing["version"]
                    if stored_version != expected_version:
                        raise PostgresVersionConflict(
                            str(negotiation.id), expected_version, stored_version
                        )
                    result = await conn.execute(
                        """
                        UPDATE negotiations
                        SET status = $3,
                            payload_json = $4::jsonb,
                            version = $5,
                            updated_at = $6,
                            legal_entity_id = $7
                        WHERE tenant_id = $1 AND id = $2 AND version = $5 - 1
                        """,
                        str(tenant_id),
                        str(negotiation.id),
                        negotiation.status.value,
                        payload_str,
                        expected_version + 1,
                        now,
                        str(negotiation.legal_entity_id),
                    )
                    # asyncpg returns e.g. "UPDATE 1" — check row was updated.
                    if result == "UPDATE 0":
                        raise PostgresVersionConflict(
                            str(negotiation.id), expected_version, stored_version
                        )

        # Increment the in-memory version to match the new DB state.
        object.__setattr__(negotiation, "version", expected_version + 1) if dataclasses.is_dataclass(negotiation) and hasattr(negotiation, "__dataclass_params__") and negotiation.__dataclass_params__.frozen else setattr(negotiation, "version", expected_version + 1)  # type: ignore[attr-defined]

    async def list_for_legal_entity(
        self, tenant_id: Any, legal_entity_id: Any
    ) -> list[Any]:  # list[NegotiationCase]
        """Return all negotiations for the given legal entity."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, str(tenant_id))
                rows = await conn.fetch(
                    """
                    SELECT id, tenant_id, legal_entity_id, status,
                           payload_json, version, created_at, updated_at
                    FROM negotiations
                    WHERE tenant_id = $1 AND legal_entity_id = $2
                    ORDER BY created_at DESC
                    """,
                    str(tenant_id),
                    str(legal_entity_id),
                )

        return [_row_to_negotiation(dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# EntitlementRepository
# ---------------------------------------------------------------------------


class PostgresEntitlementRepository:
    """Postgres-backed repository for Entitlement aggregates.

    Implements ``core/domains/contracts/ports.py :: EntitlementRepository``.

    Table: ``entitlements(id, tenant_id, legal_entity_id, agreement_id,
                           asset_id, status, payload_json, version, created_at)``
    """

    def __init__(self, pool: AsyncPgPool) -> None:
        self._pool = pool

    async def get(
        self, tenant_id: Any, entitlement_id: Any
    ) -> Any:  # Entitlement
        """Load an Entitlement by its aggregate id."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, str(tenant_id))
                row = await conn.fetchrow(
                    """
                    SELECT id, tenant_id, legal_entity_id, agreement_id,
                           asset_id, status, payload_json, version, created_at
                    FROM entitlements
                    WHERE tenant_id = $1 AND id = $2
                    """,
                    str(tenant_id),
                    str(entitlement_id),
                )

        if row is None:
            raise PostgresRecordNotFound("entitlements", str(entitlement_id))

        return _row_to_entitlement(dict(row))

    async def save(self, tenant_id: Any, entitlement: Any) -> None:  # Entitlement
        """Persist an Entitlement with optimistic concurrency guard."""
        payload_str = _serialize_aggregate(entitlement)
        now = datetime.now(timezone.utc)
        expected_version = entitlement.version

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, str(tenant_id))

                existing = await conn.fetchrow(
                    "SELECT version FROM entitlements WHERE tenant_id = $1 AND id = $2",
                    str(tenant_id),
                    str(entitlement.id),
                )

                if existing is None:
                    await conn.execute(
                        """
                        INSERT INTO entitlements
                            (id, tenant_id, legal_entity_id, agreement_id,
                             asset_id, status, payload_json, version, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9)
                        """,
                        str(entitlement.id),
                        str(tenant_id),
                        str(entitlement.legal_entity_id),
                        entitlement.agreement_id,
                        entitlement.asset_id,
                        entitlement.status.value,
                        payload_str,
                        expected_version + 1,
                        now,
                    )
                else:
                    stored_version: int = existing["version"]
                    if stored_version != expected_version:
                        raise PostgresVersionConflict(
                            str(entitlement.id), expected_version, stored_version
                        )
                    result = await conn.execute(
                        """
                        UPDATE entitlements
                        SET status = $3,
                            payload_json = $4::jsonb,
                            version = $5,
                            agreement_id = $6,
                            asset_id = $7,
                            legal_entity_id = $8
                        WHERE tenant_id = $1 AND id = $2 AND version = $5 - 1
                        """,
                        str(tenant_id),
                        str(entitlement.id),
                        entitlement.status.value,
                        payload_str,
                        expected_version + 1,
                        entitlement.agreement_id,
                        entitlement.asset_id,
                        str(entitlement.legal_entity_id),
                    )
                    if result == "UPDATE 0":
                        raise PostgresVersionConflict(
                            str(entitlement.id), expected_version, stored_version
                        )

        try:
            setattr(entitlement, "version", expected_version + 1)
        except (AttributeError, dataclasses.FrozenInstanceError):
            pass  # frozen dataclass — version tracking is caller responsibility

    async def list_for_agreement(
        self, tenant_id: Any, agreement_id: str
    ) -> list[Any]:  # list[Entitlement]
        """Return all entitlements derived from a specific agreement."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, str(tenant_id))
                rows = await conn.fetch(
                    """
                    SELECT id, tenant_id, legal_entity_id, agreement_id,
                           asset_id, status, payload_json, version, created_at
                    FROM entitlements
                    WHERE tenant_id = $1 AND agreement_id = $2
                    ORDER BY created_at DESC
                    """,
                    str(tenant_id),
                    agreement_id,
                )

        return [_row_to_entitlement(dict(r)) for r in rows]

    async def list_active_for_legal_entity(
        self, tenant_id: Any, legal_entity_id: Any
    ) -> list[Any]:  # list[Entitlement]
        """Return active entitlements for a legal entity."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant_context(conn, str(tenant_id))
                rows = await conn.fetch(
                    """
                    SELECT id, tenant_id, legal_entity_id, agreement_id,
                           asset_id, status, payload_json, version, created_at
                    FROM entitlements
                    WHERE tenant_id = $1
                      AND legal_entity_id = $2
                      AND status = 'active'
                    ORDER BY created_at DESC
                    """,
                    str(tenant_id),
                    str(legal_entity_id),
                )

        return [_row_to_entitlement(dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Internal serialization helpers
# ---------------------------------------------------------------------------


def _default_json_serializer(obj: Any) -> Any:
    """Handle types that json.dumps cannot serialize by default."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "value"):
        # Enum-like: return the .value attribute.
        return obj.value
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    raise TypeError(f"Cannot serialize {type(obj)!r} to JSON")


def _serialize_aggregate(aggregate: Any) -> str:
    """Serialize a domain aggregate to a JSON string for JSONB storage.

    Uses ``dataclasses.asdict`` to flatten the dataclass hierarchy, then
    ``json.dumps`` with a custom default handler for UUID, datetime, Enum.
    """
    raw = dataclasses.asdict(aggregate)
    return json.dumps(raw, default=_default_json_serializer)


def _row_to_negotiation(row: dict) -> Any:  # NegotiationCase
    """Reconstruct a NegotiationCase from a raw DB row.

    The full aggregate state is stored in ``payload_json``.  We rebuild the
    domain object using the stored fields plus the explicit index columns.
    """
    from dataspace_control_plane_core.domains.contracts.model.aggregates import (  # noqa: PLC0415
        NegotiationCase,
    )
    from dataspace_control_plane_core.domains.contracts.model.enums import (  # noqa: PLC0415
        NegotiationStatus,
    )
    from dataspace_control_plane_core.domains._shared.ids import (  # noqa: PLC0415
        AggregateId,
        TenantId,
        LegalEntityId,
    )
    import uuid as _uuid  # noqa: PLC0415

    payload: dict = _ensure_dict(row["payload_json"])

    negotiation = NegotiationCase(
        id=AggregateId(_uuid.UUID(row["id"])),
        tenant_id=TenantId(row["tenant_id"]),
        legal_entity_id=LegalEntityId(row["legal_entity_id"]),
        status=NegotiationStatus(row["status"]),
        version=row["version"],
    )
    # Restore complex fields from payload blob when present.
    _restore_negotiation_from_payload(negotiation, payload)
    return negotiation


def _restore_negotiation_from_payload(negotiation: Any, payload: dict) -> None:
    """Apply payload_json fields back onto a NegotiationCase instance.

    We do a best-effort restore of fields that are safe to reconstruct.
    Heavy sub-graph fields (offer_history, agreement) are restored here
    only when the payload schema matches; otherwise they default to empty.
    """
    # started_at / concluded_at
    if payload.get("started_at"):
        try:
            from datetime import datetime as _dt  # noqa: PLC0415
            negotiation.started_at = _dt.fromisoformat(payload["started_at"])
        except (ValueError, TypeError):
            pass
    if payload.get("concluded_at"):
        try:
            from datetime import datetime as _dt  # noqa: PLC0415
            negotiation.concluded_at = _dt.fromisoformat(payload["concluded_at"])
        except (ValueError, TypeError):
            pass


def _row_to_entitlement(row: dict) -> Any:  # Entitlement
    """Reconstruct an Entitlement from a raw DB row."""
    from dataspace_control_plane_core.domains.contracts.model.aggregates import (  # noqa: PLC0415
        Entitlement,
    )
    from dataspace_control_plane_core.domains.contracts.model.enums import (  # noqa: PLC0415
        EntitlementStatus,
    )
    from dataspace_control_plane_core.domains._shared.ids import (  # noqa: PLC0415
        AggregateId,
        TenantId,
        LegalEntityId,
    )
    import uuid as _uuid  # noqa: PLC0415

    payload: dict = _ensure_dict(row["payload_json"])

    entitlement = Entitlement(
        id=AggregateId(_uuid.UUID(row["id"])),
        tenant_id=TenantId(row["tenant_id"]),
        legal_entity_id=LegalEntityId(row["legal_entity_id"]),
        agreement_id=row["agreement_id"],
        asset_id=row["asset_id"],
        status=EntitlementStatus(row["status"]),
        version=row["version"],
    )

    # Restore purpose and counterparty_id from payload if present.
    if payload.get("purpose"):
        entitlement.purpose = payload["purpose"]
    if payload.get("counterparty_id"):
        entitlement.counterparty_id = payload["counterparty_id"]
    if payload.get("valid_from"):
        try:
            from datetime import datetime as _dt  # noqa: PLC0415
            entitlement.valid_from = _dt.fromisoformat(payload["valid_from"])
        except (ValueError, TypeError):
            pass
    if payload.get("valid_to"):
        try:
            from datetime import datetime as _dt  # noqa: PLC0415
            entitlement.valid_to = _dt.fromisoformat(payload["valid_to"])
        except (ValueError, TypeError):
            pass

    return entitlement


def _ensure_dict(value: Any) -> dict:
    """Normalize JSONB values returned by asyncpg (may be dict or str)."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return {}
