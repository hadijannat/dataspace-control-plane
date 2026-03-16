"""
Lifespan: initialize and tear down shared resources.

Startup is intentionally tolerant: the app can boot in tests or local dev even
when Temporal or Postgres are unavailable, and dependent routes will return
HTTP 503 until those resources are healthy.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from dataspace_control_plane_adapters.infrastructure.postgres.api import (
    AsyncPgPool,
    PostgresAuditSink,
    PostgresIdempotencyRepository,
    PostgresPoolSettings,
    PostgresProcedureRuntimeRepository,
    PostgresSchemaChecker,
)
from fastapi import FastAPI
from temporalio.client import Client as TemporalClient

from app.settings import settings
from app.services.procedure_catalog import ProcedureCatalog

logger = structlog.get_logger(__name__)

def _normalize_database_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("startup.begin", host=settings.temporal_host, namespace=settings.temporal_namespace)

    app.state.temporal_client = None
    app.state.database_pool = None
    app.state.procedure_catalog = ProcedureCatalog.discover()
    app.state.idempotency_repository = None
    app.state.procedure_runtime_repository = None
    app.state.audit_sink = None
    app.state.resource_status = {
        "temporal": False,
        "database": False,
        "procedure_catalog": bool(app.state.procedure_catalog.available_types()),
    }

    try:
        pool = AsyncPgPool(
            PostgresPoolSettings(
                dsn=_normalize_database_url(settings.database_url),
                min_size=1,
                max_size=5,
                statement_timeout_ms=30_000,
            )
        )
        await pool.open()
        readiness = await PostgresSchemaChecker(pool).verify_required_state(
            required_tables=("procedures", "http_idempotency_keys", "audit_records"),
            required_version=3,
        )
        if not readiness.is_ready:
            if readiness.missing_tables:
                raise RuntimeError(
                    "database schema missing required tables: "
                    + ", ".join(readiness.missing_tables)
                )
            raise RuntimeError(
                "database schema version is behind the required migration level: "
                f"current={readiness.current_version} required={readiness.required_version}"
            )
        app.state.database_pool = pool
        app.state.idempotency_repository = PostgresIdempotencyRepository(pool)
        app.state.procedure_runtime_repository = PostgresProcedureRuntimeRepository(pool)
        app.state.audit_sink = PostgresAuditSink(pool)
        app.state.resource_status["database"] = True
        logger.info("startup.database_connected")
    except Exception as exc:
        logger.warning("startup.database_unavailable", error=str(exc))

    try:
        app.state.temporal_client = await TemporalClient.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
        )
        app.state.resource_status["temporal"] = True
        logger.info("startup.temporal_connected")
    except Exception as exc:
        logger.warning("startup.temporal_unavailable", error=str(exc))
    yield

    logger.info("shutdown.begin")
    if app.state.database_pool is not None:
        await app.state.database_pool.close()
    logger.info("shutdown.complete")
