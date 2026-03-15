"""Typed control/query messages for in-flight procedures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId

from .workflow_contracts import ProcedureSnapshot


@dataclass(frozen=True)
class CancelProcedure:
    tenant_id: TenantId
    workflow_id: WorkflowId
    actor: ActorRef
    correlation: CorrelationContext
    reason: str


@dataclass(frozen=True)
class ApproveProcedure:
    tenant_id: TenantId
    workflow_id: WorkflowId
    actor: ActorRef
    correlation: CorrelationContext
    comment: str = ""


@dataclass(frozen=True)
class RejectProcedure:
    tenant_id: TenantId
    workflow_id: WorkflowId
    actor: ActorRef
    correlation: CorrelationContext
    reason: str


@dataclass(frozen=True)
class RetryProcedure:
    tenant_id: TenantId
    workflow_id: WorkflowId
    actor: ActorRef
    correlation: CorrelationContext
    reason: str = ""


@dataclass(frozen=True)
class PauseProcedure:
    tenant_id: TenantId
    workflow_id: WorkflowId
    actor: ActorRef
    correlation: CorrelationContext
    reason: str = ""


@dataclass(frozen=True)
class ResumeProcedure:
    tenant_id: TenantId
    workflow_id: WorkflowId
    actor: ActorRef
    correlation: CorrelationContext
    reason: str = ""


@dataclass(frozen=True)
class ProcedureQuery:
    tenant_id: TenantId
    workflow_id: WorkflowId
    correlation: CorrelationContext
    include_payload: bool = False


@dataclass(frozen=True)
class ProcedureQueryResponse:
    snapshot: ProcedureSnapshot
    metadata: dict[str, Any] = field(default_factory=dict)
