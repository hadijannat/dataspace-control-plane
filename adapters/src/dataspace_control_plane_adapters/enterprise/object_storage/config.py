"""Configuration for the object storage adapter (S3-compatible)."""
from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

from ..._shared.config import AdapterSettings


class ObjectStorageSettings(AdapterSettings):
    """Settings for S3-compatible object storage.

    Compatible with AWS S3, MinIO, Ceph RGW, and any S3-compatible endpoint.
    All fields sourced from environment variables prefixed with OBJECT_STORAGE_.
    """

    model_config = SettingsConfigDict(
        env_prefix="OBJECT_STORAGE_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    endpoint_url: str | None = Field(
        None,
        description=(
            "Custom S3-compatible endpoint URL (e.g. http://minio:9000). "
            "If None, uses AWS S3 default endpoint."
        ),
    )
    region: str = Field("us-east-1", description="AWS region or MinIO region.")
    access_key_id: str = Field(..., description="AWS access key ID or MinIO user.")
    secret_access_key: SecretStr = Field(..., description="AWS secret access key.")
    session_token: SecretStr | None = Field(
        None, description="STS session token for temporary credentials."
    )
    default_bucket: str = Field(..., description="Default bucket name.")
    use_path_style: bool = Field(
        False,
        description=(
            "Use path-style URLs (http://host/bucket/key) instead of "
            "virtual-hosted style (http://bucket.host/key). "
            "Required for MinIO when not behind a load-balancer."
        ),
    )
    multipart_threshold_bytes: int = Field(
        64 * 1024 * 1024,  # 64 MiB
        description="File size threshold above which multipart upload is used.",
        ge=5 * 1024 * 1024,  # S3 minimum part size
    )
    multipart_chunk_bytes: int = Field(
        16 * 1024 * 1024,  # 16 MiB
        description="Part size for multipart uploads.",
        ge=5 * 1024 * 1024,
    )
