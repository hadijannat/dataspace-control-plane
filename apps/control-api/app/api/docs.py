from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse

from app.api.deps.auth import get_current_principal
from app.settings import settings


def register_docs_routes(app: FastAPI) -> None:
    if settings.docs_public or settings.debug:

        @app.get("/openapi.json", include_in_schema=False)
        async def openapi_json() -> JSONResponse:
            return JSONResponse(app.openapi())

        @app.get("/docs", include_in_schema=False)
        async def swagger_ui():
            return get_swagger_ui_html(
                openapi_url="/openapi.json",
                title=f"{app.title} - Swagger UI",
            )

        @app.get("/redoc", include_in_schema=False)
        async def redoc_ui():
            return get_redoc_html(
                openapi_url="/openapi.json",
                title=f"{app.title} - ReDoc",
            )

        return

    @app.get("/openapi.json", include_in_schema=False, dependencies=[Depends(get_current_principal)])
    async def authed_openapi_json() -> JSONResponse:
        return JSONResponse(app.openapi())

    @app.get("/docs", include_in_schema=False, dependencies=[Depends(get_current_principal)])
    async def authed_swagger_ui():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Swagger UI",
        )

    @app.get("/redoc", include_in_schema=False, dependencies=[Depends(get_current_principal)])
    async def authed_redoc_ui():
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - ReDoc",
        )

