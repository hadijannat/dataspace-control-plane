"""Keycloak adapter configuration.

All settings are read from environment variables with the ``KEYCLOAK_`` prefix.

Example .env::

    KEYCLOAK_BASE_URL=https://auth.example.com
    KEYCLOAK_REALM=dataspace
    KEYCLOAK_CLIENT_ID=control-plane
    KEYCLOAK_CLIENT_SECRET=super-secret
    KEYCLOAK_JWKS_CACHE_TTL_S=300
    KEYCLOAK_ADMIN_CLIENT_ID=admin-cli
"""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import SettingsConfigDict

from dataspace_control_plane_adapters._shared.config import AdapterSettings


class KeycloakSettings(AdapterSettings):
    """Configuration block for the Keycloak human-IAM adapter.

    Subclasses ``AdapterSettings`` (pydantic-settings).  Source priority:
    environment variables > .env file > defaults.

    All variables must be prefixed with ``KEYCLOAK_`` (case-insensitive).
    """

    model_config = SettingsConfigDict(
        env_prefix="KEYCLOAK_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    base_url: AnyHttpUrl = Field(
        ...,
        description="Base URL of the Keycloak server, e.g. https://auth.example.com",
    )
    realm: str = Field(
        ...,
        description="Keycloak realm name, e.g. 'dataspace'",
    )
    client_id: str = Field(
        ...,
        description="OIDC client ID used for token verification audience check",
    )
    client_secret: SecretStr = Field(
        ...,
        description="OIDC client secret (used for client-credentials Admin API token requests)",
    )
    jwks_cache_ttl_s: int = Field(
        300,
        ge=10,
        description="JWKS cache TTL in seconds (default 300 = 5 minutes)",
    )
    admin_client_id: str = Field(
        "admin-cli",
        description="Keycloak client ID for Admin REST API access",
    )

    # ------------------------------------------------------------------
    # Derived URL helpers (not environment-settable)
    # ------------------------------------------------------------------

    @property
    def jwks_uri(self) -> str:
        """JWKS endpoint URL for the configured realm."""
        return f"{str(self.base_url).rstrip('/')}/realms/{self.realm}/protocol/openid-connect/certs"

    @property
    def token_endpoint(self) -> str:
        """Token endpoint URL for client-credentials grants."""
        return f"{str(self.base_url).rstrip('/')}/realms/{self.realm}/protocol/openid-connect/token"

    @property
    def openid_config_uri(self) -> str:
        """OIDC Discovery endpoint URL."""
        return (
            f"{str(self.base_url).rstrip('/')}/realms/{self.realm}"
            "/.well-known/openid-configuration"
        )

    @property
    def issuer(self) -> str:
        """Expected OIDC issuer URL for JWT verification."""
        return f"{str(self.base_url).rstrip('/')}/realms/{self.realm}"

    @property
    def admin_base_url(self) -> str:
        """Admin REST API base URL for this realm."""
        return f"{str(self.base_url).rstrip('/')}/admin/realms/{self.realm}"
