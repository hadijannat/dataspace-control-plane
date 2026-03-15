from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CONTROL_API_", env_file=".env", extra="ignore")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    public_base_url: str = "http://localhost:8000"

    # OIDC / Keycloak
    oidc_issuer: AnyHttpUrl = Field(
        "http://localhost:8080/realms/dataspace",
        description="Keycloak realm issuer URL",
    )
    oidc_audience: str = "control-api"
    oidc_jwks_cache_ttl: int = 300  # seconds
    keycloak_browser_url: str = "http://localhost:8080"
    keycloak_browser_realm: str = "dataspace"
    keycloak_browser_client_id: str = "web-console"

    # Temporal
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_tls: bool = False

    # Database (read models)
    database_url: str = "postgresql://postgres:postgres@localhost:5432/control_plane"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # UI bootstrap
    tenant_banner: str | None = None

    # API docs
    docs_public: bool = False

    # Streams
    stream_poll_interval_seconds: float = 2.0
    stream_ticket_secret: str = "dev-stream-ticket-secret"
    stream_ticket_ttl_seconds: int = 300

    # Webhooks
    webhook_shared_secret: str | None = None

    # Telemetry
    otel_endpoint: str | None = None
    otel_service_name: str = "control-api"


settings = Settings()
