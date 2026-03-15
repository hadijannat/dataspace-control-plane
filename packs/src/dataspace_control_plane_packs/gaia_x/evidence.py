"""Gaia-X evidence augmenter."""
from __future__ import annotations

from typing import Any

from .._shared.interfaces import EvidenceAugmenter
from .baseline.trust_framework import GX_TRUST_FRAMEWORK_VERSION


class GaiaXEvidenceAugmenter:
    """Augments evidence bundles with Gaia-X provenance fields."""

    def augment(
        self, evidence: dict[str, Any], *, activation_scope: str
    ) -> dict[str, Any]:
        result = dict(evidence)
        result["gx:participant_did"] = evidence.get("participant_did") or evidence.get("issuer_did") or ""
        result["gx:compliance_credential_ref"] = evidence.get("compliance_credential_ref") or ""
        result["gx:trust_framework_version"] = GX_TRUST_FRAMEWORK_VERSION
        result["gx:pack_version"] = "22.10.0"
        result["gx:activation_scope"] = activation_scope
        return result
