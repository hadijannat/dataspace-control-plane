"""Retry policy primitives for activity and workflow contracts."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_interval_seconds: int = 5
    backoff_coefficient: float = 2.0
    max_interval_seconds: int = 60
    non_retryable_error_codes: tuple[str, ...] = ()
