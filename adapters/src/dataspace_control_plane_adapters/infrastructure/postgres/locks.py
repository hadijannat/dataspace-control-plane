"""Transaction-level advisory locks for Postgres.

Advisory locks are used to coordinate:
1. Migration runners — only one process runs schema migrations at a time.
2. Singleton projections — only one process rebuilds a read model at a time.
3. Any other cross-process critical section backed by Postgres.

All locks are **transaction-level** (``pg_advisory_xact_lock``), meaning they
are automatically released when the enclosing transaction commits or rolls back.
This is safer than session-level locks because it does not require explicit
UNLOCK calls and does not leak if the application crashes.

Usage::

    async with pool.acquire() as conn:
        async with conn.transaction():
            await acquire_advisory_lock(conn, MIGRATION_LOCK_KEY)
            # ... run migration steps ...
        # lock auto-released on transaction end

Design decisions
----------------
- We use integer lock keys instead of string keys to match the Postgres
  ``pg_advisory_xact_lock(bigint)`` signature.
- Well-known lock keys are defined as module-level constants so that all code
  uses the same key without magic numbers.
- ``try_advisory_lock`` returns ``False`` instead of blocking — useful for
  polling loops that should skip work if another instance is running.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Well-known lock keys (deterministic, never change once assigned)
# ---------------------------------------------------------------------------

MIGRATION_LOCK_KEY: int = 42_001
"""Held by the migration runner while schema migrations are applied.

Only one process (e.g. the ``provisioning-agent`` or a k8s init-container)
should hold this lock at a time.
"""

GRANT_PROJECTION_LOCK_KEY: int = 42_002
"""Held while rebuilding the operator grant read-model projection."""

AUDIT_ARCHIVAL_LOCK_KEY: int = 42_003
"""Held by the audit archival job to prevent concurrent archival runs."""


# ---------------------------------------------------------------------------
# Lock helpers
# ---------------------------------------------------------------------------


async def acquire_advisory_lock(conn: Any, lock_key: int) -> None:
    """Block until the advisory lock for ``lock_key`` is acquired.

    The lock is transaction-level and automatically released when the current
    transaction ends (commit or rollback).

    Parameters
    ----------
    conn:
        An asyncpg connection inside an open transaction.
    lock_key:
        64-bit integer lock identifier.  Use the module-level constants.

    Raises
    ------
    asyncpg exceptions on connection failure (not caught here — callers handle).
    """
    await conn.execute("SELECT pg_advisory_xact_lock($1)", lock_key)


async def try_advisory_lock(conn: Any, lock_key: int) -> bool:
    """Try to acquire the advisory lock without blocking.

    Returns ``True`` if the lock was acquired, ``False`` if another session
    already holds it.

    The lock is transaction-level and automatically released on transaction end.

    Parameters
    ----------
    conn:
        An asyncpg connection inside an open transaction.
    lock_key:
        64-bit integer lock identifier.  Use the module-level constants.
    """
    row = await conn.fetchrow("SELECT pg_try_advisory_xact_lock($1) AS acquired", lock_key)
    return bool(row["acquired"])
