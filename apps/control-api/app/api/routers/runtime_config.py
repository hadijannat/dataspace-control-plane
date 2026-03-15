from fastapi import APIRouter

from app.api.schemas.runtime_config import UiRuntimeConfig
from app.settings import settings

router = APIRouter(include_in_schema=False)


@router.get("/ui/runtime-config.json", response_model=UiRuntimeConfig)
async def get_runtime_config() -> UiRuntimeConfig:
    return UiRuntimeConfig(
        apiBaseUrl=settings.public_base_url,
        keycloakUrl=settings.keycloak_browser_url,
        keycloakRealm=settings.keycloak_browser_realm,
        keycloakClientId=settings.keycloak_browser_client_id,
        tenantBanner=settings.tenant_banner,
    )

