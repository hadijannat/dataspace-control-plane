from __future__ import annotations
from dataclasses import dataclass, field

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId
from .enums import CompliancePosture
from .value_objects import ComplianceSnapshot


@dataclass
class ComplianceRecord(AggregateRoot):
    """
    Aggregate root for a tenant/legal-entity compliance posture.
    Collects successive snapshots; current_posture reflects the latest.
    """
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId("__unset__"))
    snapshots: list[ComplianceSnapshot] = field(default_factory=list)
    current_posture: CompliancePosture = CompliancePosture.UNKNOWN

    def record_scan(self, snapshot: ComplianceSnapshot) -> None:
        """Append a new compliance snapshot and update the current posture."""
        self.snapshots.append(snapshot)
        self.current_posture = snapshot.posture

    def latest_snapshot(self) -> ComplianceSnapshot | None:
        """Return the most recently recorded snapshot, or None if none exist."""
        if not self.snapshots:
            return None
        return self.snapshots[-1]


@dataclass(frozen=True)
class RequirementDefinition:
    pack_id: str
    pack_version: str
    rule_id: str
    description: str


@dataclass(frozen=True)
class ControlDefinition:
    control_id: str
    requirement_rule_id: str
    description: str


@dataclass(frozen=True)
class RequirementSet:
    requirements: tuple[RequirementDefinition, ...] = ()


@dataclass(frozen=True)
class AssessmentRun:
    run_id: str
    pack_id: str
    pack_version: str


@dataclass(frozen=True)
class AssessmentResult:
    run_id: str
    passed: bool


@dataclass(frozen=True)
class RemediationPlan:
    plan_id: str
    actions: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceRequirement:
    requirement_rule_id: str
    evidence_type: str
