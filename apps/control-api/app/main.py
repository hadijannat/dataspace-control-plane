"""FastAPI application factory."""
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.docs import register_docs_routes
from app.api.routers.runtime_config import router as runtime_config_router
from app.settings import settings
from app.lifespan import lifespan
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.exception_mapping import install_exception_handlers
from app.api.routers.health import router as health_router
from app.api.routers.operator import router as operator_router
from app.api.routers.public import router as public_router
from app.api.routers.streams import router as streams_router
from app.api.routers.webhooks import router as webhooks_router

log = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Dataspace Control Plane API",
        version="0.1.0",
        description="Single backend entrypoint for human operators and automation.",
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    # Middleware (outermost to innermost)
    app.add_middleware(CorrelationMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_exception_handlers(app)
    register_docs_routes(app)

    # Routers
    app.include_router(health_router)
    app.include_router(runtime_config_router)
    app.include_router(operator_router, prefix="/api/v1/operator", tags=["operator"])
    app.include_router(public_router, prefix="/api/v1/public", tags=["public"])
    app.include_router(streams_router, prefix="/api/v1/streams", tags=["streams"])
    app.include_router(webhooks_router, prefix="/api/v1/webhooks", tags=["webhooks"])

    return app


app = create_app()
