"""Configuration for the Tractus-X composition adapter."""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field
from dataspace_control_plane_adapters._shared.config import AdapterSettings


class TractuXSettings(AdapterSettings):
    """Settings for the Tractus-X / Catena-X ecosystem adapter."""

    dataspace_discovery_url: AnyHttpUrl = Field(
        ..., description="Tractus-X Discovery Service URL"
    )
    edc_management_url: AnyHttpUrl = Field(
        ..., description="Own EDC management API URL"
    )
    bpn: str = Field(..., description="Own Business Partner Number (BPN/L)")
    environment: str = Field(
        "dev", description="Tractus-X environment: dev | int | pre-prod | prod"
    )
    request_timeout_s: float = Field(30.0, description="HTTP request timeout in seconds")

    model_config = {"env_prefix": "TRACTUSX_"}
