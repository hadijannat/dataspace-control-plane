from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId, AggregateId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext


class ProcedureType(str, Enum):
    COMPANY_ONBOARDING = "company-onboarding"
    CONNECTOR_BOOTSTRAP = "connector-bootstrap"
    MACHINE_CREDENTIAL_ROTATION = "machine-credential-rotation"
    ASSET_TWIN_PUBLICATION = "asset-twin-publication"
    CONTRACT_NEGOTIATION = "contract-negotiation"
    COMPLIANCE_GAP_SCAN = "compliance-gap-scan"
    STALE_NEGOTIATION_SWEEP = "stale-negotiation-sweep"


class ProcedureStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True)
class ProcedureHandle:
    workflow_id: WorkflowId
    procedure_type: ProcedureType
    tenant_id: TenantId
    correlation: CorrelationContext
    run_id: str = ""
    task_queue: str = ""


@dataclass(frozen=True)
class ProcedureInput:
    tenant_id: TenantId
    procedure_type: ProcedureType
    payload: dict[str, Any]
    actor: ActorRef
    correlation: CorrelationContext
    idempotency_key: str = ""


@dataclass(frozen=True)
class ProcedureResult:
    workflow_id: WorkflowId
    status: ProcedureStatus
    output: dict[str, Any] = field(default_factory=dict)
    error_code: str = ""
    error_message: str = ""
