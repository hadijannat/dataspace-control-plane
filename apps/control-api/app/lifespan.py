"""
Lifespan: initialize and tear down shared resources.

Startup is intentionally tolerant: the app can boot in tests or local dev even
when Temporal or Postgres are unavailable, and dependent routes will return
HTTP 503 until those resources are healthy.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
import structlog
from fastapi import FastAPI
from temporalio.client import Client as TemporalClient

from app.settings import settings
from app.services.idempotency import IdempotencyStore
from app.services.procedure_catalog import ProcedureCatalog
from app.services.sse_broker import SSEBroker

logger = structlog.get_logger(__name__)

def _normalize_database_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("startup.begin", host=settings.temporal_host, namespace=settings.temporal_namespace)

    app.state.temporal_client = None
    app.state.database_pool = None
    app.state.procedure_catalog = ProcedureCatalog.discover()
    app.state.sse_broker = SSEBroker()
    app.state.idempotency_store = IdempotencyStore(ttl_seconds=86400)
    app.state.resource_status = {
        "temporal": False,
        "database": False,
        "procedure_catalog": bool(app.state.procedure_catalog.available_types()),
        "sse_broker": True,
    }

    try:
        app.state.database_pool = await asyncpg.create_pool(
            dsn=_normalize_database_url(settings.database_url),
            min_size=1,
            max_size=5,
            command_timeout=30,
        )
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

    logger.info("startup.sse_broker_ready")

    yield

    logger.info("shutdown.begin")
    if app.state.database_pool is not None:
        await app.state.database_pool.close()
    if app.state.sse_broker is not None:
        await app.state.sse_broker.close()
    logger.info("shutdown.complete")
