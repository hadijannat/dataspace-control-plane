"""asyncpg connection pool wrapper for the Postgres infrastructure adapter.

All database access in this adapter goes through AsyncPgPool.  The pool owns
the connection lifecycle; callers acquire short-lived connections via the
``acquire()`` async context manager and never hold references across
await-free checkpoints.

Configuration is via PostgresPoolSettings (pydantic-settings), which reads
environment variables prefixed with ``POSTGRES_``.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from dataspace_control_plane_adapters._shared.config import AdapterSettings

logger = logging.getLogger(__name__)


class PostgresPoolSettings(AdapterSettings):
    """Configuration for the asyncpg connection pool.

    Environment variables (all prefixed ``POSTGRES_``):
    - POSTGRES_DSN           — full asyncpg DSN, e.g. postgresql://user:pass@host/db
    - POSTGRES_MIN_SIZE      — minimum pool size (default 2)
    - POSTGRES_MAX_SIZE      — maximum pool size (default 20)
    - POSTGRES_SSL_MODE      — ``disable`` | ``prefer`` | ``require`` (default ``prefer``)
    - POSTGRES_STATEMENT_TIMEOUT_MS — per-statement timeout in ms (default 30 000)
    """

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    dsn: str = Field(..., description="asyncpg connection DSN")
    min_size: int = Field(2, ge=1, description="Minimum pool connections")
    max_size: int = Field(20, ge=1, description="Maximum pool connections")
    ssl_mode: str = Field("prefer", description="SSL mode: disable | prefer | require")
    statement_timeout_ms: int = Field(
        30_000, ge=0, description="Per-statement timeout in milliseconds"
    )


class AsyncPgPool:
    """asyncpg connection pool with convenience query helpers.

    Lifecycle
    ---------
    Use as an async context manager:

        async with AsyncPgPool(settings) as pool:
            result = await pool.fetch("SELECT ...")

    Or manage manually:

        pool = AsyncPgPool(settings)
        await pool.open()
        ...
        await pool.close()

    All queries pass through ``execute``, ``fetch``, or ``fetchrow`` — never
    use the underlying asyncpg pool directly from outside this class.
    """

    def __init__(self, settings: PostgresPoolSettings) -> None:
        self._settings = settings
        self._pool: Any = None  # asyncpg.Pool — imported lazily

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def open(self) -> None:
        """Create the underlying asyncpg pool.  Called by __aenter__."""
        import asyncpg  # noqa: PLC0415 — lazy import to keep startup cheap

        ssl: Any = None
        if self._settings.ssl_mode == "require":
            import ssl as _ssl  # noqa: PLC0415

            ssl = _ssl.create_default_context()
        elif self._settings.ssl_mode == "prefer":
            ssl = "prefer"
        # "disable" → ssl=None

        self._pool = await asyncpg.create_pool(
            dsn=self._settings.dsn,
            min_size=self._settings.min_size,
            max_size=self._settings.max_size,
            ssl=ssl,
            command_timeout=self._settings.statement_timeout_ms / 1000,
        )
        logger.info(
            "asyncpg pool opened: min=%d max=%d",
            self._settings.min_size,
            self._settings.max_size,
        )

    async def close(self) -> None:
        """Gracefully close all pool connections.  Called by __aexit__."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("asyncpg pool closed")

    async def __aenter__(self) -> "AsyncPgPool":
        await self.open()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Connection acquisition
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Any, None]:
        """Yield a single asyncpg Connection from the pool.

        The connection is returned to the pool when the context exits.
        Callers must not hold the connection across multiple async checkpoints
        without explicit transaction management.

        Usage::

            async with pool.acquire() as conn:
                await set_tenant_context(conn, tenant_id)
                rows = await pool.fetch_with(conn, "SELECT ...")
        """
        assert self._pool is not None, "Pool is not open — call open() or use as context manager"
        async with self._pool.acquire() as conn:
            yield conn

    # ------------------------------------------------------------------
    # Convenience helpers (pool-managed connections)
    # ------------------------------------------------------------------

    async def execute(self, sql: str, *args: Any) -> None:
        """Execute a statement that returns no rows."""
        assert self._pool is not None, "Pool is not open"
        await self._pool.execute(sql, *args)

    async def fetch(self, sql: str, *args: Any) -> list[dict]:
        """Execute a SELECT and return all rows as plain dicts."""
        assert self._pool is not None, "Pool is not open"
        rows = await self._pool.fetch(sql, *args)
        return [dict(r) for r in rows]

    async def fetchrow(self, sql: str, *args: Any) -> dict | None:
        """Execute a SELECT and return at most one row as a plain dict."""
        assert self._pool is not None, "Pool is not open"
        row = await self._pool.fetchrow(sql, *args)
        return dict(row) if row is not None else None

    # ------------------------------------------------------------------
    # Per-connection helpers (used with acquire())
    # ------------------------------------------------------------------

    @staticmethod
    async def execute_with(conn: Any, sql: str, *args: Any) -> None:
        """Execute a statement on an already-acquired connection."""
        await conn.execute(sql, *args)

    @staticmethod
    async def fetch_with(conn: Any, sql: str, *args: Any) -> list[dict]:
        """Fetch all rows using an already-acquired connection."""
        rows = await conn.fetch(sql, *args)
        return [dict(r) for r in rows]

    @staticmethod
    async def fetchrow_with(conn: Any, sql: str, *args: Any) -> dict | None:
        """Fetch one row using an already-acquired connection."""
        row = await conn.fetchrow(sql, *args)
        return dict(row) if row is not None else None
