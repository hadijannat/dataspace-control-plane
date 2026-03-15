"""No-op decorator helpers for runtime binding code outside ``core``."""
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

F = TypeVar("F", bound=Callable[..., object])


def procedure_binding(fn: F) -> F:
    """Marker decorator for worker/runtime registration layers."""
    return fn
