from pydantic import BaseModel


class UiRuntimeConfig(BaseModel):
    apiBaseUrl: str
    keycloakUrl: str
    keycloakRealm: str
    keycloakClientId: str
    tenantBanner: str | None = None

