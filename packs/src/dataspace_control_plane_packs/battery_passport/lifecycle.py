"""Battery lifecycle model for EU Battery Regulation.

Defines the valid lifecycle states and transition rules for battery passports
under Regulation (EU) 2023/1542. The lifecycle governs when the passport
must be updated and when it ceases (upon recycling completion).

Reference: Regulation (EU) 2023/1542
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from .._shared.rule_model import RuleViolation, ValidationResult


class BatteryState(str, Enum):
    """Valid lifecycle states for a battery passport."""

    ACTIVE = "ACTIVE"
    """Battery is in active use (first life or subsequent life)."""

    REPURPOSED = "REPURPOSED"
    """Battery has been repurposed for a different application (second life)."""

    REMANUFACTURED = "REMANUFACTURED"
    """Battery has been remanufactured (cells/modules replaced or reconditioned)."""

    WASTE = "WASTE"
    """Battery has been declared end-of-life and sent to waste processing."""

    RECYCLED_CEASED = "RECYCLED_CEASED"
    """Recycling completed — passport is terminal and ceases to be active."""


# Allowed state transitions. Each entry is (from_state, to_state, trigger).
_TRANSITIONS: list[dict[str, Any]] = [
    {
        "from": BatteryState.ACTIVE.value,
        "to": BatteryState.REPURPOSED.value,
        "trigger": "repurposing_event",
        "conditions": ["successor_passport_issued"],
    },
    {
        "from": BatteryState.ACTIVE.value,
        "to": BatteryState.REMANUFACTURED.value,
        "trigger": "remanufacturing_event",
        "conditions": ["successor_passport_issued"],
    },
    {
        "from": BatteryState.ACTIVE.value,
        "to": BatteryState.WASTE.value,
        "trigger": "end_of_life_declaration",
        "conditions": [],
    },
    {
        "from": BatteryState.REPURPOSED.value,
        "to": BatteryState.REMANUFACTURED.value,
        "trigger": "remanufacturing_event",
        "conditions": ["successor_passport_issued"],
    },
    {
        "from": BatteryState.REPURPOSED.value,
        "to": BatteryState.WASTE.value,
        "trigger": "end_of_life_declaration",
        "conditions": [],
    },
    {
        "from": BatteryState.REMANUFACTURED.value,
        "to": BatteryState.WASTE.value,
        "trigger": "end_of_life_declaration",
        "conditions": [],
    },
    {
        "from": BatteryState.WASTE.value,
        "to": BatteryState.RECYCLED_CEASED.value,
        "trigger": "recycling_completed",
        "conditions": [],
    },
]

# Set of allowed (from, to) tuples for fast lookup
_ALLOWED_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    (t["from"], t["to"]) for t in _TRANSITIONS
)

# RECYCLED_CEASED is terminal — no transitions out
_TERMINAL_STATES: frozenset[str] = frozenset([BatteryState.RECYCLED_CEASED.value])


class BatteryLifecycleProvider:
    """LifecycleModelProvider for EU Battery Regulation battery passports.

    Defines the state machine for battery passport lifecycle as specified
    in Regulation (EU) 2023/1542.
    """

    def states(self) -> list[str]:
        """Return all valid battery passport state names."""
        return [s.value for s in BatteryState]

    def transitions(self) -> list[dict[str, Any]]:
        """Return all allowed transitions as {from, to, trigger, conditions} dicts."""
        return list(_TRANSITIONS)

    def validate_transition(
        self,
        current_state: str,
        target_state: str,
        *,
        context: dict[str, Any],
    ) -> ValidationResult:
        """Check whether a transition from ``current_state`` to ``target_state`` is allowed.

        Args:
            current_state: Current battery passport lifecycle state.
            target_state: Desired target state.
            context: Arbitrary context dict (may include ``battery_id``).

        Returns:
            ValidationResult with violations if the transition is not permitted.
        """
        battery_id = context.get("battery_id", "unknown")
        result = ValidationResult(subject_id=str(battery_id))

        # Terminal state check
        if current_state in _TERMINAL_STATES:
            result.add(
                RuleViolation(
                    rule_id="battery:lifecycle-terminal-state",
                    severity="error",
                    message=(
                        f"Battery {battery_id!r} is in terminal state {current_state!r}. "
                        "No further transitions are permitted."
                    ),
                    context={
                        "battery_id": battery_id,
                        "current_state": current_state,
                        "target_state": target_state,
                    },
                )
            )
            return result

        if (current_state, target_state) not in _ALLOWED_TRANSITIONS:
            allowed_targets = [
                t["to"] for t in _TRANSITIONS if t["from"] == current_state
            ]
            result.add(
                RuleViolation(
                    rule_id="battery:lifecycle-invalid-transition",
                    severity="error",
                    message=(
                        f"Transition from {current_state!r} to {target_state!r} is not "
                        f"permitted for battery {battery_id!r}. "
                        f"Allowed targets from {current_state!r}: {allowed_targets}"
                    ),
                    context={
                        "battery_id": battery_id,
                        "current_state": current_state,
                        "target_state": target_state,
                        "allowed_targets": allowed_targets,
                    },
                )
            )

        return result
