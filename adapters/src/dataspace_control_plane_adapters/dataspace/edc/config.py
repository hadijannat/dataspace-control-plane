"""EDC adapter configuration.

EdcSettings aligns field names with the EDC SPI convention:
  web.http.<context>.auth.type = tokenbased
  web.http.<context>.auth.key  = <api_key>

All fields are read from environment variables prefixed with ``EDC_``.
"""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import SettingsConfigDict

from ..._shared.config import AdapterSettings


class EdcSettings(AdapterSettings):
    """Configuration for the EDC Management API adapter.

    Environment variable precedence (highest first): env vars, .env file, defaults.
    All env vars must be prefixed with ``EDC_``.

    Example::
        EDC_MANAGEMENT_URL=http://edc:9191/management
        EDC_PUBLIC_URL=http://edc:9291/public
        EDC_PROTOCOL_URL=http://edc:8282/protocol
        EDC_API_KEY=super-secret-key
    """

    model_config = SettingsConfigDict(
        env_prefix="EDC_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    management_url: AnyHttpUrl = Field(
        ...,
        description="EDC Management API base URL (e.g. http://edc:9191/management)",
    )
    public_url: AnyHttpUrl = Field(
        ...,
        description="EDC public data-plane endpoint (e.g. http://edc:9291/public)",
    )
    protocol_url: AnyHttpUrl = Field(
        ...,
        description="EDC DSP protocol endpoint (e.g. http://edc:8282/protocol)",
    )
    api_key: SecretStr = Field(
        ...,
        description=(
            "API key sent as X-Api-Key header — "
            "aligns with EDC web.http.<context>.auth.type=tokenbased"
        ),
    )
    page_size: int = Field(
        50,
        ge=1,
        le=500,
        description="Default page size for EDC list endpoints",
    )
    request_timeout_s: float = Field(
        30.0,
        gt=0,
        description="HTTP request timeout in seconds for all EDC management calls",
    )
