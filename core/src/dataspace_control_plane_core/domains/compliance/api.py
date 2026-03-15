"""Public API surface for compliance domain. Only import from here."""
from .model.enums import ComplianceFramework, GapSeverity, CompliancePosture
from .model.value_objects import ComplianceGap, ComplianceSnapshot, Gap, ScanScope
from .model.aggregates import (
    AssessmentResult,
    AssessmentRun,
    ComplianceRecord,
    ControlDefinition,
    EvidenceRequirement,
    RemediationPlan,
    RequirementDefinition,
    RequirementSet,
)
from .model.invariants import require_non_empty_scope
from .commands import TriggerGapScanCommand, RecordScanResultCommand
from .events import GapScanTriggered, GapScanCompleted, CompliancePostureChanged
from .errors import ComplianceRecordNotFoundError, ScanAlreadyRunningError
from .ports import (
    AssessmentEnginePort,
    ComplianceRecordRepository,
    ComplianceReportPort,
    EvidenceLocatorPort,
    GapScannerPort,
    RequirementProvider,
)
from .services import ComplianceService

__all__ = [
    "ComplianceFramework",
    "GapSeverity",
    "CompliancePosture",
    "ComplianceGap", "Gap",
    "ScanScope",
    "ComplianceSnapshot",
    "ComplianceRecord",
    "RequirementDefinition",
    "ControlDefinition",
    "RequirementSet",
    "AssessmentRun",
    "AssessmentResult",
    "RemediationPlan",
    "EvidenceRequirement",
    "require_non_empty_scope",
    "TriggerGapScanCommand",
    "RecordScanResultCommand",
    "GapScanTriggered",
    "GapScanCompleted",
    "CompliancePostureChanged",
    "ComplianceRecordNotFoundError",
    "ScanAlreadyRunningError",
    "ComplianceRecordRepository",
    "GapScannerPort", "ComplianceReportPort",
    "RequirementProvider", "EvidenceLocatorPort", "AssessmentEnginePort",
    "ComplianceService",
]
