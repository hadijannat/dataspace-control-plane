"""Configuration for the SQL extract adapter."""
from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

from ..._shared.config import AdapterSettings


class SqlExtractSettings(AdapterSettings):
    """Settings for the SQL (PostgreSQL) data extraction adapter.

    All fields sourced from environment variables prefixed with SQL_EXTRACT_.
    Supports both snapshot (full-table) and incremental (watermark/CDC) modes.
    """

    model_config = SettingsConfigDict(
        env_prefix="SQL_EXTRACT_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = Field("localhost", description="PostgreSQL host.")
    port: int = Field(5432, description="PostgreSQL port.", ge=1, le=65535)
    database: str = Field(..., description="Database name.")
    username: str = Field(..., description="Database username.")
    password: SecretStr = Field(..., description="Database password.")
    source_schema: str = Field(
        "public",
        description="Source PostgreSQL schema to extract from (env: SQL_EXTRACT_SOURCE_SCHEMA).",
    )
    snapshot_chunk_size: int = Field(
        5000,
        description="Number of rows per snapshot chunk for memory-bounded extraction.",
        ge=100,
    )
    watermark_column: str = Field(
        "updated_at",
        description=(
            "Column used for incremental extraction. Must be indexed and monotonically "
            "increasing (e.g. updated_at, id)."
        ),
    )
    cdc_slot_name: str = Field(
        "dataspace_cdc",
        description="PostgreSQL logical replication slot name for CDC mode.",
    )
    cdc_publication_name: str = Field(
        "dataspace_pub",
        description="PostgreSQL publication name for CDC mode.",
    )
    ssl_mode: str = Field(
        "prefer",
        description="PostgreSQL SSL mode: disable, allow, prefer, require, verify-ca, verify-full.",
    )

    @property
    def dsn(self) -> str:
        """Construct a PostgreSQL DSN string."""
        return (
            f"postgresql://{self.username}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.ssl_mode}"
        )
