"""Global exception handlers and error response schemas."""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)


class ErrorDetail(BaseModel):
    code: str
    message: str
    correlation_id: str | None = None


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = request.state.__dict__.get("correlation_id")
        logger.error(
            "unhandled_exception",
            path=request.url.path,
            error=str(exc),
            correlation_id=correlation_id,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                correlation_id=correlation_id,
            ).model_dump(),
        )
