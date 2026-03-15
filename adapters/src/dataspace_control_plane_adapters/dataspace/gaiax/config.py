"""Configuration for the Gaia-X trust and compliance adapter."""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field
from pydantic_settings import SettingsConfigDict
from dataspace_control_plane_adapters._shared.config import AdapterSettings


class GaiaXSettings(AdapterSettings):
    """Settings for the Gaia-X trust and compliance adapter.

    Federation profile is configuration, not a code fork.
    Different Gaia-X federations (AISBL, Catena-X, etc.) are selected by
    changing federation_id — no code changes required.
    """

    compliance_service_url: AnyHttpUrl = Field(
        ..., description="Gaia-X Compliance Service URL"
    )
    trust_anchor_registry_url: AnyHttpUrl = Field(
        ..., description="Gaia-X Trust Anchor Registry URL"
    )
    federation_id: str = Field(
        "gaia-x-eu",
        description="Federation identifier; determines which trust anchor set is active",
    )
    request_timeout_s: float = Field(30.0, description="HTTP request timeout in seconds")

    model_config = SettingsConfigDict(
        env_prefix="GAIAX_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )
