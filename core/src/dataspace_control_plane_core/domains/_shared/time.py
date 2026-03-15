"""
Clock abstraction. Use Clock in domain services; inject UtcClock in production,
a fake in tests. Never call datetime.now() directly in domain or service code.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """Pluggable clock for domain services."""

    def now(self) -> datetime:
        """Return the current UTC datetime."""
        ...


class UtcClock:
    """Production UTC clock."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FrozenClock:
    """Test-only clock that always returns the same instant."""

    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed
