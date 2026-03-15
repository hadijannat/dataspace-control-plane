"""Vault KMS adapter configuration.

All Vault connection parameters are loaded from environment variables
with the VAULT_ prefix.  Secrets (token, role credentials) are typed
as SecretStr so they are never printed in logs or repr output.
"""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import SettingsConfigDict

from dataspace_control_plane_adapters._shared.config import AdapterSettings


class VaultSettings(AdapterSettings):
    """Configuration for the Vault KMS infrastructure adapter.

    Source order (highest wins): environment variables, .env file, defaults.
    All env vars are prefixed with VAULT_ (case-insensitive).
    """

    model_config = SettingsConfigDict(
        env_prefix="VAULT_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    vault_addr: AnyHttpUrl = Field(
        default="http://localhost:8200",
        description="Base URL for the Vault server.",
    )
    vault_token: SecretStr = Field(
        ...,
        description="Vault root or service token. Use AppRole in production.",
    )
    # AppRole auth (alternative to static token; both fields optional together)
    approle_role_id: str | None = Field(
        None,
        description="AppRole role_id for Vault authentication. Set alongside approle_secret_id.",
    )
    approle_secret_id: SecretStr | None = Field(
        None,
        description="AppRole secret_id for Vault authentication.",
    )

    transit_mount: str = Field(
        default="transit",
        description="Mount path of the Vault Transit secrets engine.",
    )
    pki_mount: str = Field(
        default="pki",
        description="Mount path of the Vault PKI secrets engine.",
    )
    pki_role: str = Field(
        default="dataspace-service",
        description="PKI role name used when issuing X.509 certificates.",
    )
    # TLS for Vault connection
    tls_ca_cert: str | None = Field(
        None,
        description="Path to CA bundle PEM for verifying the Vault server certificate.",
    )
    tls_client_cert: str | None = Field(
        None,
        description="Path to client certificate PEM for mTLS to Vault.",
    )
    tls_client_key: str | None = Field(
        None,
        description="Path to client private key PEM for mTLS to Vault.",
    )
    tls_verify: bool = Field(
        True,
        description="Whether to verify the Vault server TLS certificate.",
    )
    # HTTP tuning
    request_timeout_s: float = Field(
        30.0,
        description="HTTP request timeout in seconds for Vault API calls.",
    )
