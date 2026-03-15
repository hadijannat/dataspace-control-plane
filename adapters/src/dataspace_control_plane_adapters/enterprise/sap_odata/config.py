"""Configuration for the SAP OData adapter."""
from __future__ import annotations

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import SettingsConfigDict

from ..._shared.config import AdapterSettings


class SapOdataSettings(AdapterSettings):
    """Settings for the SAP OData 4.01 source adapter.

    All fields are sourced from environment variables prefixed with SAP_ODATA_.
    Example service_url: https://host/sap/opu/odata/sap/SERVICE/
    """

    model_config = SettingsConfigDict(
        env_prefix="SAP_ODATA_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    service_url: AnyHttpUrl = Field(
        ...,
        description="Base URL of the OData service, including trailing slash.",
    )
    username: str = Field(..., description="SAP user for Basic auth.")
    password: SecretStr = Field(..., description="SAP password for Basic auth.")
    metadata_cache_ttl_s: int = Field(
        3600,
        description="How long (seconds) to cache $metadata before re-fetching.",
        ge=0,
    )
    page_size: int = Field(
        1000,
        description="Number of records to request per OData page ($top).",
        ge=1,
    )
