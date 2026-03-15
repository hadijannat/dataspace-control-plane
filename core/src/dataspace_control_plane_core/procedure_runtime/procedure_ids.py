"""Stable identifiers and procedure types for durable execution contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId


class ProcedureType(str, Enum):
    COMPANY_ONBOARDING = "company-onboarding"
    CONNECTOR_BOOTSTRAP = "connector-bootstrap"
    MACHINE_CREDENTIAL_ROTATION = "machine-credential-rotation"
    ASSET_TWIN_PUBLICATION = "asset-twin-publication"
    CONTRACT_NEGOTIATION = "contract-negotiation"
    COMPLIANCE_GAP_SCAN = "compliance-gap-scan"
    STALE_NEGOTIATION_SWEEP = "stale-negotiation-sweep"


@dataclass(frozen=True)
class ProcedureHandle:
    workflow_id: WorkflowId
    procedure_type: ProcedureType
    tenant_id: TenantId
    correlation: CorrelationContext
    run_id: str = ""
    task_queue: str = ""
