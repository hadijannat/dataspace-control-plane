from datetime import datetime
from typing import Protocol, runtime_checkable

from dataspace_control_plane_core.domains._shared.ids import TenantId

from .exports import EvidenceExport
from .manifests import EvidenceManifest
from .records import AuditCategory, AuditRecord
from .signing import SignatureRef


@runtime_checkable
class AuditSinkPort(Protocol):
    """Append-only sink. Storage remains outside ``core``."""

    async def emit(self, record: AuditRecord) -> None:
        ...


@runtime_checkable
class AuditQueryPort(Protocol):
    """Read-only query interface for operator and compliance views."""

    async def list_records(
        self,
        tenant_id: TenantId,
        category: AuditCategory | None,
        from_dt: datetime,
        to_dt: datetime,
        limit: int = 100,
    ) -> list[AuditRecord]:
        ...

    async def get_record(self, tenant_id: TenantId, record_id: str) -> AuditRecord:
        ...


@runtime_checkable
class ManifestSignerPort(Protocol):
    """Sign manifests or exports via KMS/Vault adapters."""

    async def sign_manifest(self, manifest: EvidenceManifest) -> SignatureRef:
        ...

    async def sign_export(self, export: EvidenceExport) -> SignatureRef:
        ...
