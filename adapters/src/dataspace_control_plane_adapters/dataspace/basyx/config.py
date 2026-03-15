"""BaSyx adapter configuration.

All fields are read from environment variables prefixed with ``BASYX_``.
"""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import SettingsConfigDict

from ..._shared.config import AdapterSettings


class BasYxSettings(AdapterSettings):
    """Configuration for the BaSyx AAS adapter.

    Environment variable precedence (highest first): env vars, .env file, defaults.
    All env vars must be prefixed with ``BASYX_``.

    Example::
        BASYX_AAS_REGISTRY_URL=http://localhost:8082
        BASYX_SUBMODEL_REGISTRY_URL=http://localhost:8083
        BASYX_SUBMODEL_REPOSITORY_URL=http://localhost:8081
        BASYX_API_KEY=my-api-key
    """

    model_config = SettingsConfigDict(
        env_prefix="BASYX_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    aas_registry_url: AnyHttpUrl = Field(
        "http://localhost:8082",
        description="BaSyx AAS Registry service base URL",
    )
    submodel_registry_url: AnyHttpUrl = Field(
        "http://localhost:8083",
        description="BaSyx Submodel Registry service base URL",
    )
    submodel_repository_url: AnyHttpUrl = Field(
        "http://localhost:8081",
        description="BaSyx Submodel Repository service base URL",
    )
    api_key: SecretStr | None = Field(
        None,
        description="Optional API key for BaSyx security extension (X-API-KEY header)",
    )
    request_timeout_s: float = Field(
        30.0,
        gt=0,
        description="HTTP request timeout in seconds for all BaSyx calls",
    )
    probe_timeout_s: float = Field(
        5.0,
        gt=0,
        description="Timeout in seconds for endpoint health probes",
    )
