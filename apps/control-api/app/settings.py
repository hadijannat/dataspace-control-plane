from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CONTROL_API_", env_file=".env", extra="ignore")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # OIDC / Keycloak
    oidc_issuer: AnyHttpUrl = Field(
        "http://localhost:8080/realms/dataspace",
        description="Keycloak realm issuer URL",
    )
    oidc_audience: str = "control-api"
    oidc_jwks_cache_ttl: int = 300  # seconds

    # Temporal
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_tls: bool = False

    # Database (read models)
    database_url: str = "postgresql://postgres:postgres@localhost:5432/control_plane"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # Telemetry
    otel_endpoint: str | None = None
    otel_service_name: str = "control-api"


settings = Settings()
