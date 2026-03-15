from __future__ import annotations
from dataclasses import dataclass
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from .model.value_objects import ScanScope, ComplianceSnapshot


@dataclass(frozen=True)
class TriggerGapScanCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    scope: ScanScope
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class RecordScanResultCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    snapshot: ComplianceSnapshot
    actor: ActorRef
    correlation: CorrelationContext
