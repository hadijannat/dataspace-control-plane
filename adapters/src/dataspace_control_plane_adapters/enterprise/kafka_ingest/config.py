"""Configuration for the Kafka ingest adapter."""
from __future__ import annotations

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import SettingsConfigDict

from ..._shared.config import AdapterSettings


class KafkaSettings(AdapterSettings):
    """Settings for the Kafka event ingestion adapter.

    All fields are sourced from environment variables prefixed with KAFKA_.
    Idempotence constraints are enforced as hard defaults: acks=all,
    enable.idempotence=True, max_in_flight<=5, retries>0.
    """

    model_config = SettingsConfigDict(
        env_prefix="KAFKA_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    bootstrap_servers: str = Field(
        "localhost:9092",
        description="Comma-separated list of Kafka broker addresses.",
    )
    security_protocol: str = Field(
        "PLAINTEXT",
        description="Security protocol: PLAINTEXT, SSL, SASL_SSL, or SASL_PLAINTEXT.",
    )
    sasl_mechanism: str | None = Field(
        None,
        description="SASL mechanism: PLAIN, SCRAM-SHA-256, SCRAM-SHA-512, GSSAPI, etc.",
    )
    sasl_username: str | None = Field(None, description="SASL username.")
    sasl_password: SecretStr | None = Field(None, description="SASL password.")
    ssl_ca_location: str | None = Field(
        None, description="Path to CA certificate file for SSL verification."
    )
    consumer_group_id: str = Field(
        "dataspace-control-plane",
        description="Kafka consumer group ID.",
    )
    consumer_auto_offset_reset: str = Field(
        "earliest",
        description="Consumer auto.offset.reset: earliest or latest.",
    )
    # Producer idempotence configuration — these are defaults, not opt-ins.
    producer_acks: str = Field(
        "all",
        description=(
            "Producer acks setting. MUST be 'all' when enable.idempotence=True. "
            "Changing this to a non-'all' value while keeping idempotence enabled "
            "will raise a validation error."
        ),
    )
    producer_enable_idempotence: bool = Field(
        True,
        description=(
            "Enable producer idempotence. When True (default), enforces acks=all, "
            "retries>0, and max_in_flight<=5."
        ),
    )
    producer_max_in_flight: int = Field(
        5,
        description=(
            "Max in-flight requests per connection. MUST be <=5 when idempotence is enabled."
        ),
        ge=1,
    )
    producer_retries: int = Field(
        2_147_483_647,
        description="Number of retries for transient producer errors.",
        ge=1,
    )

    @model_validator(mode="after")
    def _enforce_idempotence_constraints(self) -> "KafkaSettings":
        """Validate that acks=all and max_in_flight<=5 when idempotence is enabled."""
        if self.producer_enable_idempotence:
            if self.producer_acks != "all":
                raise ValueError(
                    "producer_acks must be 'all' when producer_enable_idempotence=True. "
                    f"Got: '{self.producer_acks}'"
                )
            if self.producer_max_in_flight > 5:
                raise ValueError(
                    "producer_max_in_flight must be <=5 when producer_enable_idempotence=True. "
                    f"Got: {self.producer_max_in_flight}"
                )
        return self
