from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RotationStartInput:
    tenant_id: str
    legal_entity_id: str
    credential_profile: str
    rotation_interval_days: int = 90
    look_ahead_days: int = 30
    idempotency_key: str = ""


@dataclass(frozen=True)
class RotationResult:
    workflow_id: str
    status: str
    rotated_count: int = 0
    next_rotation_at: str = ""


@dataclass(frozen=True)
class RotationStatusQuery:
    rotation_state: str
    expiring_count: int
    rotated_count: int
    next_rotation_at: str
    is_paused: bool


@dataclass
class RotationCarryState:
    """Carry-over state for Continue-As-New boundaries."""
    rotation_state: str
    last_rotation_at: str
    rotated_count_total: int
    is_paused: bool = False
    dedupe_ids: set[str] = field(default_factory=set)
    iteration: int = 0
