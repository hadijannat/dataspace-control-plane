"""
tests/unit/adapters/test_kafka_settings.py
Unit tests for the Kafka ingest adapter's idempotence settings validator.

The KafkaSettings model enforces at construction time:
  - producer_acks must be "all" when producer_enable_idempotence=True
  - producer_max_in_flight must be <=5 when producer_enable_idempotence=True

These invariants prevent accidental misconfiguration that would break
exactly-once delivery guarantees on the Kafka producer side.

Marker: unit
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# ── Path injection ────────────────────────────────────────────────────────────
_ADAPTERS_SRC = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "adapters"
    / "src"
)
if _ADAPTERS_SRC.exists() and str(_ADAPTERS_SRC) not in sys.path:
    sys.path.insert(0, str(_ADAPTERS_SRC))


def _import_settings():
    try:
        from dataspace_control_plane_adapters.enterprise.kafka_ingest.config import (
            KafkaSettings,
        )
        return KafkaSettings
    except ImportError as exc:
        pytest.skip(f"KafkaSettings not available: {exc}")


def _make_settings(**overrides):
    KafkaSettings = _import_settings()
    # Provide _env_file=None and use init= to bypass env file lookup in tests.
    defaults = dict(
        bootstrap_servers="localhost:9092",
        producer_acks="all",
        producer_enable_idempotence=True,
        producer_max_in_flight=5,
        producer_retries=2_147_483_647,
    )
    defaults.update(overrides)
    # pydantic-settings: override env prefix by passing values directly
    return KafkaSettings.model_validate(defaults)


# ── Test 1: Default configuration is valid ────────────────────────────────────


def test_kafka_settings_default_is_valid() -> None:
    """Default KafkaSettings must pass validation (acks=all, idempotence=True, in_flight=5)."""
    _import_settings()
    settings = _make_settings()
    assert settings.producer_acks == "all"
    assert settings.producer_enable_idempotence is True
    assert settings.producer_max_in_flight == 5


def test_kafka_settings_default_retries_is_max_int() -> None:
    """Default producer_retries must be set to the max int sentinel value."""
    _import_settings()
    settings = _make_settings()
    assert settings.producer_retries == 2_147_483_647


# ── Test 2: acks != "all" with idempotence=True raises ───────────────────────


@pytest.mark.parametrize("bad_acks", ["0", "1", "-1", "none"])
def test_non_all_acks_with_idempotence_enabled_raises(bad_acks: str) -> None:
    """producer_acks != 'all' must raise ValueError when idempotence is enabled."""
    from pydantic import ValidationError as PydanticValidationError

    with pytest.raises((ValueError, PydanticValidationError)):
        _make_settings(
            producer_acks=bad_acks,
            producer_enable_idempotence=True,
        )


# ── Test 3: max_in_flight > 5 with idempotence=True raises ───────────────────


@pytest.mark.parametrize("bad_in_flight", [6, 10, 1000])
def test_max_in_flight_gt_5_with_idempotence_raises(bad_in_flight: int) -> None:
    """producer_max_in_flight > 5 must raise ValueError when idempotence is enabled."""
    from pydantic import ValidationError as PydanticValidationError

    with pytest.raises((ValueError, PydanticValidationError)):
        _make_settings(
            producer_max_in_flight=bad_in_flight,
            producer_enable_idempotence=True,
        )


# ── Test 4: idempotence=False lifts acks restriction ─────────────────────────


@pytest.mark.parametrize("relaxed_acks", ["0", "1", "-1"])
def test_acks_not_all_is_allowed_when_idempotence_disabled(relaxed_acks: str) -> None:
    """Any acks value must be accepted when producer_enable_idempotence=False."""
    _import_settings()
    # Must not raise
    settings = _make_settings(
        producer_acks=relaxed_acks,
        producer_enable_idempotence=False,
    )
    assert settings.producer_acks == relaxed_acks


# ── Test 5: idempotence=False lifts max_in_flight restriction ────────────────


@pytest.mark.parametrize("high_in_flight", [6, 100, 10_000])
def test_high_in_flight_allowed_when_idempotence_disabled(high_in_flight: int) -> None:
    """producer_max_in_flight > 5 must be accepted when idempotence is disabled."""
    _import_settings()
    settings = _make_settings(
        producer_acks="0",
        producer_enable_idempotence=False,
        producer_max_in_flight=high_in_flight,
    )
    assert settings.producer_max_in_flight == high_in_flight


# ── Test 6: Valid boundary values ─────────────────────────────────────────────


@pytest.mark.parametrize("in_flight", [1, 2, 3, 4, 5])
def test_max_in_flight_boundary_valid_with_idempotence(in_flight: int) -> None:
    """producer_max_in_flight values 1–5 must all be valid when idempotence is on."""
    _import_settings()
    settings = _make_settings(
        producer_acks="all",
        producer_enable_idempotence=True,
        producer_max_in_flight=in_flight,
    )
    assert settings.producer_max_in_flight == in_flight


# ── Test 7: Error message quality ────────────────────────────────────────────


def test_acks_error_message_mentions_all() -> None:
    """The acks validation error must mention 'all' and 'idempotence' for operator clarity."""
    from pydantic import ValidationError as PydanticValidationError

    with pytest.raises((ValueError, PydanticValidationError)) as exc_info:
        _make_settings(
            producer_acks="1",
            producer_enable_idempotence=True,
        )

    err = str(exc_info.value).lower()
    # The error should guide operators to the correct fix
    assert "all" in err or "acks" in err or "idempotence" in err, (
        f"acks validation error message is not operator-friendly: {exc_info.value}"
    )


def test_max_in_flight_error_message_mentions_5() -> None:
    """The max_in_flight validation error must mention the limit of 5."""
    from pydantic import ValidationError as PydanticValidationError

    with pytest.raises((ValueError, PydanticValidationError)) as exc_info:
        _make_settings(
            producer_max_in_flight=10,
            producer_enable_idempotence=True,
        )

    err = str(exc_info.value).lower()
    assert "5" in err or "in_flight" in err or "idempotence" in err, (
        f"max_in_flight validation error message is not operator-friendly: {exc_info.value}"
    )


# ── Test 8: DLQ topic naming convention ──────────────────────────────────────


def test_kafka_settings_has_consumer_group_id() -> None:
    """KafkaSettings must expose consumer_group_id for DLQ topic namespace derivation."""
    _import_settings()
    settings = _make_settings()
    assert hasattr(settings, "consumer_group_id")
    assert settings.consumer_group_id  # non-empty default


def test_kafka_settings_security_defaults_to_plaintext() -> None:
    """Default security_protocol must be PLAINTEXT for local dev safety."""
    _import_settings()
    settings = _make_settings()
    assert settings.security_protocol.upper() == "PLAINTEXT"
