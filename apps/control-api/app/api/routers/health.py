from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"
    dependencies: dict[str, bool] | None = None


@router.get("/health/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=HealthResponse)
async def readiness(request: Request) -> JSONResponse:
    dependencies = getattr(request.app.state, "resource_status", {})
    ready = all(
        dependencies.get(name, False)
        for name in ("temporal", "database", "procedure_catalog", "sse_broker")
    )
    body = HealthResponse(
        status="ok" if ready else "degraded",
        dependencies=dependencies or None,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=body.model_dump(),
    )
