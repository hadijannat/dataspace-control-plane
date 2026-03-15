"""Temporal client adapter configuration.

All Temporal connection parameters are loaded from environment variables
with the TEMPORAL_ prefix.  The API key (if any) is typed as SecretStr
so it is never printed in logs or repr output.
"""
from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

from dataspace_control_plane_adapters._shared.config import AdapterSettings


class TemporalClientSettings(AdapterSettings):
    """Configuration for the Temporal client infrastructure adapter.

    Source order (highest wins): environment variables, .env file, defaults.
    All env vars are prefixed with TEMPORAL_ (case-insensitive).
    """

    model_config = SettingsConfigDict(
        env_prefix="TEMPORAL_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = Field(
        default="localhost",
        description="Temporal server hostname.",
    )
    port: int = Field(
        default=7233,
        description="Temporal server gRPC port.",
    )
    namespace: str = Field(
        default="default",
        description="Temporal namespace for all workflow operations.",
    )
    api_key: SecretStr | None = Field(
        None,
        description="Temporal Cloud API key. Only required for Temporal Cloud deployments.",
    )
    # mTLS certificate paths for self-hosted TLS or Temporal Cloud mTLS
    tls_cert_path: str | None = Field(
        None,
        description="Path to client certificate PEM for mTLS to Temporal server.",
    )
    tls_key_path: str | None = Field(
        None,
        description="Path to client private key PEM for mTLS to Temporal server.",
    )
    tls_ca_path: str | None = Field(
        None,
        description="Path to CA bundle PEM for verifying the Temporal server certificate.",
    )
    tls_server_name: str | None = Field(
        None,
        description="Override the TLS SNI server name (useful for Temporal Cloud).",
    )
    # Connection tuning
    connect_timeout_s: float = Field(
        10.0,
        description="gRPC connection timeout in seconds.",
    )
    rpc_timeout_s: float = Field(
        30.0,
        description="Default gRPC RPC timeout in seconds.",
    )
    # Default task queue used when no explicit queue is provided
    default_task_queue: str = Field(
        default="dataspace-control-plane",
        description="Default Temporal task queue name.",
    )
