"""
Clock abstraction and default-clock helpers for the semantic kernel.

Domain services should accept a ``Clock`` explicitly. Base framework-neutral
types such as events and audit records use the shared default clock so tests can
override wall time without importing runtime frameworks.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Iterator, Protocol


class Clock(Protocol):
    """Pluggable UTC clock."""

    def now(self) -> datetime:
        """Return the current UTC datetime."""
        ...


class UtcClock:
    """Production UTC clock."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FrozenClock:
    """Test clock that always returns the same instant."""

    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed.astimezone(timezone.utc)

    def now(self) -> datetime:
        return self._fixed


_DEFAULT_CLOCK: ContextVar[Clock] = ContextVar(
    "dataspace_control_plane_core_default_clock",
    default=UtcClock(),
)


def default_clock() -> Clock:
    """Return the active shared default clock."""
    return _DEFAULT_CLOCK.get()


def utc_now() -> datetime:
    """Return the current time using the shared default clock."""
    return default_clock().now()


@contextmanager
def use_clock(clock: Clock) -> Iterator[Clock]:
    """
    Temporarily override the shared default clock.

    This is mainly intended for unit tests of framework-neutral types such as
    ``DomainEvent`` and ``AuditRecord``.
    """
    token = _DEFAULT_CLOCK.set(clock)
    try:
        yield clock
    finally:
        _DEFAULT_CLOCK.reset(token)
