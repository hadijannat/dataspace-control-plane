"""Configuration for the Siemens Teamcenter adapter."""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import SettingsConfigDict

from ..._shared.config import AdapterSettings


class TeamcenterSettings(AdapterSettings):
    """Settings for the Siemens Teamcenter REST adapter.

    All fields are sourced from environment variables prefixed with TEAMCENTER_.
    Example base_url: https://teamcenter.example.com
    """

    model_config = SettingsConfigDict(
        env_prefix="TEAMCENTER_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    base_url: AnyHttpUrl = Field(
        ...,
        description="Base URL of the Teamcenter microservice gateway.",
    )
    username: str = Field(..., description="Teamcenter login username.")
    password: SecretStr = Field(..., description="Teamcenter login password.")
    chunk_size: int = Field(
        500,
        description="Maximum number of items to export per request chunk.",
        ge=1,
    )
