"""Evidence manifest models for signing and export workflows."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from dataspace_control_plane_core.domains._shared.ids import TenantId
from dataspace_control_plane_core.domains._shared.time import utc_now

from .hashing import HashDigest
from .lineage import LineageLink
from .signing import SignatureRef


@dataclass(frozen=True)
class EvidenceManifestEntry:
    item_id: str
    digest: HashDigest
    media_type: str
    storage_uri: str


@dataclass(frozen=True)
class EvidenceManifest:
    manifest_id: str
    tenant_id: TenantId
    subject_id: str
    subject_type: str
    created_at: datetime = field(default_factory=utc_now)
    entries: tuple[EvidenceManifestEntry, ...] = ()
    lineage: tuple[LineageLink, ...] = ()
    signature: SignatureRef | None = None
