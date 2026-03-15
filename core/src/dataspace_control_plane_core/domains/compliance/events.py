from __future__ import annotations
from dataclasses import dataclass
from dataspace_control_plane_core.domains._shared.events import DomainEvent
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId
from .model.enums import CompliancePosture


@dataclass(frozen=True)
class GapScanTriggered(DomainEvent, event_type="compliance.GapScanTriggered"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]
    framework_count: int = 0


@dataclass(frozen=True)
class GapScanCompleted(DomainEvent, event_type="compliance.GapScanCompleted"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]
    gap_count: int = 0
    posture: CompliancePosture = CompliancePosture.UNKNOWN


@dataclass(frozen=True)
class CompliancePostureChanged(DomainEvent, event_type="compliance.CompliancePostureChanged"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]
    previous_posture: CompliancePosture = CompliancePosture.UNKNOWN
    new_posture: CompliancePosture = CompliancePosture.UNKNOWN
