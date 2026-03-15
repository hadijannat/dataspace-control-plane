"""Backoff utilities for polling and rate-limited adapters.

Prefer tenacity-based retries for HTTP calls (see retries.py).
Use these helpers for explicit polling loops in activities (e.g. waiting for
an async negotiation state change at a DSP endpoint).
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable, Awaitable
from typing import TypeVar

T = TypeVar("T")


async def poll_until(
    check: Callable[[], Awaitable[T | None]],
    *,
    interval_s: float = 5.0,
    max_attempts: int = 60,
    timeout_s: float | None = None,
) -> T:
    """Poll `check()` until it returns a non-None result.

    Raises TimeoutError if max_attempts or timeout_s is exceeded.
    """
    total = 0.0
    for attempt in range(max_attempts):
        result = await check()
        if result is not None:
            return result
        await asyncio.sleep(interval_s)
        total += interval_s
        if timeout_s is not None and total >= timeout_s:
            raise TimeoutError(
                f"poll_until: no result after {attempt + 1} attempts ({total:.0f}s)"
            )
    raise TimeoutError(f"poll_until: no result after {max_attempts} attempts")


def exponential_intervals(
    start_s: float = 1.0,
    factor: float = 2.0,
    cap_s: float = 60.0,
) -> "Iterator[float]":
    """Yield exponential back-off intervals (infinite sequence, capped at cap_s)."""
    from typing import Iterator  # local import keeps module-level imports light

    def _gen() -> Iterator[float]:
        current = start_s
        while True:
            yield current
            current = min(current * factor, cap_s)

    return _gen()
