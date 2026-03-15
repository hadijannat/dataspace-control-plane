"""DCP adapter configuration.

All fields are read from environment variables prefixed with ``DCP_``.
"""
from __future__ import annotations

from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import SettingsConfigDict

from ..._shared.config import AdapterSettings


class DcpSettings(AdapterSettings):
    """Configuration for the DCP Credential Protocol adapter.

    Environment variable precedence (highest first): env vars, .env file, defaults.
    All env vars must be prefixed with ``DCP_``.

    Example::
        DCP_CREDENTIAL_SERVICE_URL=https://cs.example.com
        DCP_ISSUER_SERVICE_URL=https://issuer.example.com
        DCP_TRUST_ANCHOR_URLS=https://ta1.example.com,https://ta2.example.com
        DCP_KEY_ID=default
        DCP_DID_METHOD=did:web
    """

    model_config = SettingsConfigDict(
        env_prefix="DCP_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    credential_service_url: AnyHttpUrl = Field(
        ...,
        description="DCP Credential Service base URL",
    )
    issuer_service_url: AnyHttpUrl = Field(
        ...,
        description="DCP Issuer Service base URL",
    )
    trust_anchor_urls: List[str] = Field(
        default_factory=list,
        description="List of trust anchor endpoint URLs for active anchor resolution",
    )
    key_id: str = Field(
        "default",
        description="Logical key ID in VaultKeyRegistry used for SI token signing",
    )
    did_method: str = Field(
        "did:web",
        description="DID method prefix for self-issued tokens (e.g. did:web, did:key)",
    )
    request_timeout_s: float = Field(
        30.0,
        gt=0,
        description="HTTP request timeout in seconds for all DCP calls",
    )
