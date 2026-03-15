from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_STREAM_TICKET_SECRET = "dev-stream-ticket-secret"


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

    # Keycloak browser (web-console) settings
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

    # Public-facing URLs
    public_base_url: str = "http://localhost:8000"

    # UI bootstrap
    tenant_banner: str | None = None

    # API docs
    docs_public: bool = False

    # Streams
    stream_poll_interval_seconds: float = 2.0
    stream_ticket_secret: str = _DEFAULT_STREAM_TICKET_SECRET
    stream_ticket_ttl_seconds: int = 300

    # Webhooks
    webhook_shared_secret: str | None = None

    # Telemetry
    otel_endpoint: str | None = None
    otel_service_name: str = "control-api"

    @field_validator("stream_ticket_secret", mode="after")
    @classmethod
    def validate_stream_ticket_secret(cls, v: str, info) -> str:
        # In debug/dev mode all checks are skipped — default short secret is allowed.
        debug = (info.data or {}).get("debug", False)
        if debug:
            return v
        if len(v) < 32:
            raise ValueError(
                "stream_ticket_secret must be at least 32 characters long in production"
            )
        if v == _DEFAULT_STREAM_TICKET_SECRET:
            raise ValueError(
                "stream_ticket_secret must not use the default development value in production; "
                "set CONTROL_API_STREAM_TICKET_SECRET to a unique secret of ≥32 characters"
            )
        return v


settings = Settings()
