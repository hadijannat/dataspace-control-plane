"""Schema readiness checks for application startup."""
from __future__ import annotations

from dataclasses import dataclass

from dataspace_control_plane_adapters.infrastructure.postgres.pool import AsyncPgPool


@dataclass(frozen=True)
class SchemaReadiness:
    is_ready: bool
    missing_tables: tuple[str, ...] = ()
    current_version: int | None = None
    required_version: int | None = None

    @property
    def has_version_mismatch(self) -> bool:
        return (
            self.required_version is not None
            and self.current_version is not None
            and self.current_version < self.required_version
        )


class PostgresSchemaChecker:
    def __init__(self, pool: AsyncPgPool) -> None:
        self._pool = pool

    async def verify_required_tables(
        self,
        required_tables: tuple[str, ...],
    ) -> SchemaReadiness:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = ANY($1::text[])
                """,
                list(required_tables),
            )
        found = {row["table_name"] for row in rows}
        missing = tuple(sorted(set(required_tables) - found))
        return SchemaReadiness(is_ready=not missing, missing_tables=missing)

    async def verify_required_state(
        self,
        *,
        required_tables: tuple[str, ...],
        required_version: int,
    ) -> SchemaReadiness:
        table_readiness = await self.verify_required_tables(
            required_tables + ("schema_migrations",)
        )
        if not table_readiness.is_ready:
            return SchemaReadiness(
                is_ready=False,
                missing_tables=table_readiness.missing_tables,
                required_version=required_version,
            )

        async with self._pool.acquire() as conn:
            current_version = await conn.fetchval(
                "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
            )

        current_version = int(current_version or 0)
        is_ready = current_version >= required_version
        return SchemaReadiness(
            is_ready=is_ready,
            current_version=current_version,
            required_version=required_version,
        )
