"""Reusable test helpers for procedure integration tests."""
from __future__ import annotations
from typing import Any, Callable, Sequence
import asyncio


def make_fake_activity(return_value: Any) -> Callable:
    """Create a synchronous fake activity for use with ActivityEnvironment."""
    async def _fake(*args: Any, **kwargs: Any) -> Any:
        return return_value
    return _fake


class InMemoryActivityStore:
    """Records activity calls for assertion in tests."""
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def record(self, name: str, inp: Any) -> None:
        self.calls.append((name, inp))

    def called(self, name: str) -> bool:
        return any(n == name for n, _ in self.calls)

    def call_count(self, name: str) -> int:
        return sum(1 for n, _ in self.calls if n == name)
