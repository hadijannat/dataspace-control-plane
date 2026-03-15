"""DSP adapter configuration.

DspSettings carries the configuration needed by the DSP protocol adapter to
send and receive Dataspace Protocol messages. It does not configure any
vendor-specific runtime (EDC, etc.) — that is EdcSettings' responsibility.

All fields are read from environment variables prefixed with ``DSP_``.

Example::
    DSP_CALLBACK_BASE_URL=https://my-control-plane.example.com/dsp
"""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field
from pydantic_settings import SettingsConfigDict

from ..._shared.config import AdapterSettings


class DspSettings(AdapterSettings):
    """Configuration for the DSP 2025-1 protocol adapter.

    Environment variable precedence (highest first): env vars, .env file, defaults.
    All env vars must be prefixed with ``DSP_``.
    """

    model_config = SettingsConfigDict(
        env_prefix="DSP_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    callback_base_url: AnyHttpUrl = Field(
        ...,
        description=(
            "Base URL for this platform's DSP callback endpoint. "
            "DSP negotiation and transfer messages reference this URL so the "
            "remote connector can POST events back to this control plane. "
            "Example: https://control-plane.example.com/dsp"
        ),
    )
    request_timeout_s: float = Field(
        30.0,
        gt=0,
        description="HTTP request timeout in seconds for outgoing DSP calls",
    )
