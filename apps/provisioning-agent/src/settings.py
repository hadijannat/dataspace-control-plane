from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PROVISIONING_", env_file=".env", extra="ignore")

    # Control API (primary system of record once live)
    control_api_url: str = "http://localhost:8000"
    control_api_token: str | None = None  # Service account token

    # Keycloak Admin
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "master"
    keycloak_admin_client_id: str = "admin-cli"
    keycloak_admin_client_secret: str = ""

    # Target realm (where dataspace clients/roles are created)
    target_realm: str = "dataspace"

    # Temporal
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"

    # State / checkpoints
    checkpoint_dir: str = ".provisioning-checkpoints"
    desired_state_dir: str = "desired-state"

    # Dry-run default
    dry_run: bool = False

    log_level: str = "INFO"


settings = Settings()
