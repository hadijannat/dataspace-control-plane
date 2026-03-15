"""Export contracts for evidentiary audit bundles."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from dataspace_control_plane_core.domains._shared.time import utc_now

from .hashing import HashDigest
from .manifests import EvidenceManifest
from .signing import SignatureRef


@dataclass(frozen=True)
class EvidenceExport:
    export_id: str
    manifest: EvidenceManifest
    format: str
    destination_uri: str
    exported_at: datetime = field(default_factory=utc_now)
    digest: HashDigest | None = None
    signature: SignatureRef | None = None
