"""Contracts for external side-effecting activities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId


@dataclass(frozen=True)
class ActivityRequest:
    tenant_id: TenantId
    workflow_id: WorkflowId
    action: str
    payload: dict[str, Any]
    actor: ActorRef
    correlation: CorrelationContext
    idempotency_key: str
    compensation_action: str | None = None


@dataclass(frozen=True)
class ActivityResult:
    action: str
    succeeded: bool
    payload: dict[str, Any] = field(default_factory=dict)
    error_code: str = ""
    error_message: str = ""


@dataclass(frozen=True)
class CompensationRequest:
    tenant_id: TenantId
    workflow_id: WorkflowId
    action: str
    reason: str
    correlation: CorrelationContext
    idempotency_key: str


@dataclass(frozen=True)
class CompensationResult:
    action: str
    compensated: bool
    detail: dict[str, Any] = field(default_factory=dict)
