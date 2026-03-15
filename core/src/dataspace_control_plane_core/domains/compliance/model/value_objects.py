from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from .enums import ComplianceFramework, GapSeverity, CompliancePosture


@dataclass(frozen=True)
class ComplianceGap:
    gap_id: str
    framework: ComplianceFramework
    requirement_id: str
    description: str
    severity: GapSeverity
    remediation_hint: str = ""


@dataclass(frozen=True)
class ScanScope:
    frameworks: tuple[ComplianceFramework, ...]
    include_info: bool = False


@dataclass(frozen=True)
class ComplianceSnapshot:
    scanned_at: datetime
    frameworks: tuple[ComplianceFramework, ...]
    gaps: tuple[ComplianceGap, ...]
    posture: CompliancePosture
