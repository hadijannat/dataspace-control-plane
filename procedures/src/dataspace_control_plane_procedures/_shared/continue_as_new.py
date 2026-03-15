from __future__ import annotations
from dataclasses import dataclass, field
from typing import TypeVar, cast

from temporalio.converter import value_to_type

HISTORY_THRESHOLD = 9_000   # Warn at 10,240; terminate at 51,200

StartInputT = TypeVar("StartInputT")
StateSnapshotT = TypeVar("StateSnapshotT")


def should_continue_as_new(
    event_count: int,
    threshold: int = HISTORY_THRESHOLD,
) -> bool:
    return event_count >= threshold


@dataclass(frozen=True)
class CarryEnvelope:
    """Common Continue-As-New wrapper.

    The start input stays stable across runs while the state snapshot carries the
    minimal durable workflow state needed to resume safely.
    """

    start_input: object
    state: object


def unwrap_start_input(
    inp: StartInputT | CarryEnvelope,
) -> tuple[StartInputT, object | None]:
    if isinstance(inp, CarryEnvelope):
        return cast(StartInputT, inp.start_input), inp.state
    return inp, None


def coerce_workflow_input(value: object, target_type: type[StartInputT]) -> StartInputT:
    if isinstance(value, target_type):
        return value
    return value_to_type(target_type, value, [])


def decode_start_input(
    inp: object,
    *,
    start_input_type: type[StartInputT],
    state_type: type[StateSnapshotT],
) -> tuple[StartInputT, StateSnapshotT | None]:
    if isinstance(inp, CarryEnvelope):
        return (
            coerce_workflow_input(inp.start_input, start_input_type),
            coerce_workflow_input(inp.state, state_type),
        )

    if isinstance(inp, dict) and "start_input" in inp and "state" in inp:
        return (
            coerce_workflow_input(inp["start_input"], start_input_type),
            coerce_workflow_input(inp["state"], state_type),
        )

    return coerce_workflow_input(inp, start_input_type), None


@dataclass
class DedupeState:
    """Rolling set of handled message/idempotency IDs, carried across Continue-As-New.

    Internally uses a dict[str, None] to preserve insertion order (Python 3.7+),
    so eviction always removes the oldest IDs rather than arbitrary hash-ordered
    entries.  The external snapshot contract remains set[str] for compatibility.
    """
    _handled: dict[str, None] = field(default_factory=dict)
    max_size: int = 500

    def is_duplicate(self, msg_id: str) -> bool:
        return msg_id in self._handled

    def mark_handled(self, msg_id: str) -> None:
        if len(self._handled) >= self.max_size:
            # Evict oldest half by insertion order — dict preserves insertion
            # order in Python 3.7+, making eviction deterministic across runs.
            keys = list(self._handled)
            self._handled = {k: None for k in keys[len(keys) // 2:]}
        self._handled[msg_id] = None

    def snapshot(self) -> set[str]:
        return set(self._handled)

    @classmethod
    def from_snapshot(cls, snapshot: set[str], max_size: int = 500) -> "DedupeState":
        obj = cls(max_size=max_size)
        obj._handled = {k: None for k in snapshot}
        return obj
