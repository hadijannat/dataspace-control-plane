from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TEMPORAL_WORKERS_", env_file=".env", extra="ignore")

    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_tls: bool = False
    temporal_tls_cert_path: str | None = None
    temporal_tls_key_path: str | None = None

    # Worker concurrency
    max_concurrent_activities: int = 100
    max_concurrent_workflow_tasks: int = 100

    # Health / probe
    health_port: int = 8001

    # Telemetry
    otel_endpoint: str | None = None
    otel_service_name: str = "temporal-workers"

    log_level: str = "INFO"


settings = Settings()
