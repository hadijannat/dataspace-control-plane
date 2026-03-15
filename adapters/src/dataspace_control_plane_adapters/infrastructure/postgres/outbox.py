"""Transactional outbox for domain events.

The outbox pattern guarantees at-least-once event delivery without distributed
transactions: a domain event is written to ``outbox_entries`` in the **same**
database transaction as the aggregate state change, then a poller publishes
unpublished entries to the message bus (Kafka, etc.) and marks them published.

Table DDL (applied by ``V001__initial_schema.sql``):

    CREATE TABLE outbox_entries (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        aggregate_type TEXT NOT NULL,
        aggregate_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload_json JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        published_at TIMESTAMPTZ
    );

Design decisions
----------------
- ``OutboxEntry`` is a frozen dataclass (immutable value object once created).
- ``PostgresOutboxWriter.append`` takes an already-acquired connection so that
  it participates in the caller's transaction.
- ``PostgresOutboxPoller.poll_unpublished`` uses ``SELECT ... FOR UPDATE SKIP LOCKED``
  to allow multiple pollers without double-publishing.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Value object
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OutboxEntry:
    """Immutable representation of a single outbox row.

    Fields map 1-to-1 to the ``outbox_entries`` table columns.
    ``published_at`` is ``None`` until the poller successfully delivers the event.
    """

    id: str
    """Stable, unique identifier for this outbox entry (UUID string)."""

    tenant_id: str
    """Tenant that owns the emitting aggregate."""

    aggregate_type: str
    """Domain aggregate class name, e.g. ``"NegotiationCase"``."""

    aggregate_id: str
    """String representation of the aggregate's AggregateId."""

    event_type: str
    """Fully-qualified event class name, e.g. ``"contracts.AgreementConcluded"``."""

    payload_json: dict
    """Event payload serialized as a plain dict (will be stored as JSONB)."""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    """Creation timestamp (UTC)."""

    published_at: datetime | None = None
    """Set by the poller after successful publish; ``None`` means unpublished."""


# ---------------------------------------------------------------------------
# Writer (called within a repository transaction)
# ---------------------------------------------------------------------------


class PostgresOutboxWriter:
    """Appends domain events to the transactional outbox.

    This class does **not** manage connections — it receives an already-acquired
    asyncpg connection from the calling repository so that the INSERT is part of
    the same transaction as the aggregate state change.

    Port satisfaction: no core port is directly implemented here; this is an
    internal infrastructure primitive used by repository implementations.
    """

    async def append(self, conn: Any, entry: OutboxEntry) -> None:
        """Insert a single ``OutboxEntry`` into the outbox table.

        Parameters
        ----------
        conn:
            Active asyncpg connection (inside an open transaction).
        entry:
            The outbox entry to persist.

        The ``payload_json`` dict is serialized to a JSON string before
        passing to asyncpg, which then stores it as JSONB.
        """
        payload_str = json.dumps(entry.payload_json)
        await conn.execute(
            """
            INSERT INTO outbox_entries
                (id, tenant_id, aggregate_type, aggregate_id,
                 event_type, payload_json, created_at, published_at)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8)
            """,
            entry.id,
            entry.tenant_id,
            entry.aggregate_type,
            entry.aggregate_id,
            entry.event_type,
            payload_str,
            entry.created_at,
            entry.published_at,
        )


# ---------------------------------------------------------------------------
# Poller (called by background publisher process)
# ---------------------------------------------------------------------------


class PostgresOutboxPoller:
    """Reads unpublished outbox entries and marks them as delivered.

    Concurrency safety: ``SELECT ... FOR UPDATE SKIP LOCKED`` prevents multiple
    poller instances from claiming the same rows.  Each caller gets a disjoint
    batch.

    Port satisfaction: no core port; used by ``apps/temporal-workers`` publisher
    activity and the outbox CDC pipeline.
    """

    async def poll_unpublished(
        self, conn: Any, limit: int = 100
    ) -> list[OutboxEntry]:
        """Return up to ``limit`` unpublished entries, locked for this transaction.

        The caller is expected to publish each entry and then call
        ``mark_published`` within the same transaction.

        Parameters
        ----------
        conn:
            Active asyncpg connection (inside an open transaction).
        limit:
            Maximum number of entries to return per poll cycle.

        Returns
        -------
        list[OutboxEntry]
            Entries ordered by ``created_at ASC`` (oldest first).
        """
        rows = await conn.fetch(
            """
            SELECT id, tenant_id, aggregate_type, aggregate_id,
                   event_type, payload_json, created_at, published_at
            FROM outbox_entries
            WHERE published_at IS NULL
            ORDER BY created_at ASC
            LIMIT $1
            FOR UPDATE SKIP LOCKED
            """,
            limit,
        )
        return [_row_to_entry(dict(r)) for r in rows]

    async def mark_published(self, conn: Any, entry_id: str) -> None:
        """Set ``published_at`` to now() for the given entry.

        Parameters
        ----------
        conn:
            Active asyncpg connection.
        entry_id:
            The ``OutboxEntry.id`` returned from ``poll_unpublished``.
        """
        await conn.execute(
            """
            UPDATE outbox_entries
            SET published_at = NOW()
            WHERE id = $1
            """,
            entry_id,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _row_to_entry(row: dict) -> OutboxEntry:
    """Convert a raw asyncpg row dict to an ``OutboxEntry``."""
    payload = row["payload_json"]
    # asyncpg returns JSONB columns as already-parsed Python objects.
    if isinstance(payload, str):
        payload = json.loads(payload)
    return OutboxEntry(
        id=row["id"],
        tenant_id=row["tenant_id"],
        aggregate_type=row["aggregate_type"],
        aggregate_id=row["aggregate_id"],
        event_type=row["event_type"],
        payload_json=payload,
        created_at=row["created_at"],
        published_at=row.get("published_at"),
    )
