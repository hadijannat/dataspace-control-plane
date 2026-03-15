"""Shared base-configuration primitives for all concrete adapters.

Each concrete adapter defines its own Settings subclass with adapter-specific
fields. This module provides the common base and helper utilities.
"""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdapterSettings(BaseSettings):
    """Base for all adapter configuration blocks.

    Concrete adapters extend this with their specific fields.
    Source order (highest wins): environment, .env file, defaults.
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


class TlsSettings(AdapterSettings):
    """TLS configuration reused across HTTP-based adapters."""

    tls_ca_bundle: str | None = Field(None, description="Path to CA bundle PEM for custom CAs")
    tls_client_cert: str | None = Field(None, description="Path to client certificate PEM")
    tls_client_key: str | None = Field(None, description="Path to client private key PEM")
    tls_verify: bool = Field(True, description="Verify server TLS certificate")


class TokenAuthSettings(AdapterSettings):
    """Static bearer-token auth (e.g. EDC API key, Temporal API key)."""

    auth_type: str = Field("tokenbased", description="Auth type; align with EDC web.http.<ctx>.auth.type")
    auth_token: SecretStr = Field(..., description="Bearer token / API key")
    auth_header: str = Field("X-Api-Key", description="Header name carrying the token")
