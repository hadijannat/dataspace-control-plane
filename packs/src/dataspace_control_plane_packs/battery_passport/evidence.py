"""Battery passport evidence augmenter."""
from __future__ import annotations

from typing import Any

from .._shared.interfaces import EvidenceAugmenter


class BatteryEvidenceAugmenter:
    """Augments evidence bundles with battery passport provenance fields."""

    _PACK_VERSION = "2023.0958.1"
    _REGULATION_VERSION = "2023/1542"

    def augment(
        self, evidence: dict[str, Any], *, activation_scope: str
    ) -> dict[str, Any]:
        result = dict(evidence)
        result["bat:battery_id"] = evidence.get("battery_id") or ""
        result["bat:lifecycle_state"] = evidence.get("lifecycle_state") or "active"
        result["bat:passport_link_ref"] = evidence.get("successor_passport_id") or evidence.get("predecessor_passport_id") or ""
        result["bat:access_matrix_version"] = evidence.get("access_matrix_version") or "2023/1542"
        result["bat:regulation_version"] = self._REGULATION_VERSION
        result["bat:pack_version"] = self._PACK_VERSION
        result["bat:activation_scope"] = activation_scope
        return result
