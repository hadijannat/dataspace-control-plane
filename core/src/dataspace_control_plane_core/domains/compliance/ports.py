from typing import Protocol, runtime_checkable
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId
from .model.aggregates import ComplianceRecord
from .model.value_objects import ScanScope, ComplianceSnapshot


@runtime_checkable
class ComplianceRecordRepository(Protocol):
    """Persistence port for ComplianceRecord aggregate."""

    async def get(self, tenant_id: TenantId, legal_entity_id: LegalEntityId) -> ComplianceRecord: ...

    async def save(self, record: ComplianceRecord, expected_version: int) -> None: ...

    async def find_by_legal_entity(
        self, tenant_id: TenantId, legal_entity_id: LegalEntityId
    ) -> ComplianceRecord | None: ...


@runtime_checkable
class GapScannerPort(Protocol):
    """Adapter port for executing compliance gap scans."""

    async def scan(
        self,
        tenant_id: TenantId,
        legal_entity_id: LegalEntityId,
        scope: ScanScope,
    ) -> ComplianceSnapshot:
        """Execute a gap scan and return a snapshot of the results."""
        ...


@runtime_checkable
class ComplianceReportPort(Protocol):
    """Adapter port for exporting compliance reports."""

    def export_report(
        self,
        tenant_id: TenantId,
        record: ComplianceRecord,
    ) -> str:
        """Export a compliance report for the given record. Returns a URI or serialized report."""
        ...
