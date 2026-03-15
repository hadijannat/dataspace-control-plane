"""Workflow-facing durable contract models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.domains._shared.ids import LegalEntityId, TenantId, WorkflowId
from dataspace_control_plane_core.domains._shared.time import utc_now

from .procedure_ids import ProcedureHandle, ProcedureType
from .progress import ProcedureProgress


class ProcedureStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class ManualReviewState(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ProcedureVersionMarker:
    version: str
    reason: str = ""


@dataclass(frozen=True)
class ProcedureState:
    status: ProcedureStatus
    manual_review: ManualReviewState = ManualReviewState.NOT_REQUIRED
    progress: ProcedureProgress = field(default_factory=ProcedureProgress)
    attempt: int = 1
    message: str = ""
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class ProcedureInput:
    tenant_id: TenantId
    procedure_type: ProcedureType
    actor: ActorRef
    correlation: CorrelationContext
    payload: dict[str, Any] = field(default_factory=dict)
    legal_entity_id: LegalEntityId | None = None
    idempotency_key: str = ""
    pack_ids: tuple[str, ...] = ()
    requested_at: datetime = field(default_factory=utc_now)
    due_at: datetime | None = None
    expires_at: datetime | None = None


@dataclass(frozen=True)
class ProcedureResult:
    workflow_id: WorkflowId
    status: ProcedureStatus
    output: dict[str, Any] = field(default_factory=dict)
    error_code: str = ""
    error_message: str = ""
    completed_at: datetime | None = None


@dataclass(frozen=True)
class ProcedureSnapshot:
    handle: ProcedureHandle
    state: ProcedureState
    input: ProcedureInput
    result: ProcedureResult | None = None
    version_marker: ProcedureVersionMarker | None = None
