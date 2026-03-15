"""Signature references used by evidentiary manifests and exports."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from dataspace_control_plane_core.domains._shared.time import utc_now


@dataclass(frozen=True)
class SignatureRef:
    signature_id: str
    signer_key_ref: str
    algorithm: str
    signed_at: datetime = field(default_factory=utc_now)
