"""Shared retry configuration for adapter HTTP and SDK calls.

Uses tenacity for retry logic. Adapters import named retry decorators from
here rather than configuring retries inline.
"""
from __future__ import annotations

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
import logging

from .errors import AdapterTimeoutError, AdapterUnavailableError

logger = logging.getLogger(__name__)

# Retry on transient network / service errors only.
_RETRYABLE = (AdapterTimeoutError, AdapterUnavailableError)

# 3 attempts, 1 s → 2 s → 4 s (capped at 10 s)
retry_transient_short = retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# 5 attempts, up to 60 s total back-off — for provisioning-class calls.
retry_transient_long = retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
