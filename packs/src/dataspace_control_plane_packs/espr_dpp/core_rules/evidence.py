"""ESPR DPP evidence augmenter.

Stamps ESPR-specific fields onto outgoing evidence bundles for
auditability and regulatory compliance tracing.

Reference: Regulation (EU) 2024/1781 (ESPR)
"""
from __future__ import annotations

from typing import Any


class EsprEvidenceAugmenter:
    """Augments an evidence bundle with ESPR DPP-specific fields.

    Adds the following keys to the evidence dict (without removing existing keys):
      - ``espr:product_id`` — product identifier
      - ``espr:dpp_id`` — DPP unique identifier
      - ``espr:registry_ref`` — registry reference URL or None
      - ``espr:carrier_type`` — physical data carrier type
      - ``espr:regulation_version`` — always "2024/1781"
      - ``espr:backup_copy_ref`` — backup location URI or None
    """

    def augment(
        self,
        evidence: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Add ESPR DPP fields to ``evidence``. Existing keys are preserved."""
        augmented = dict(evidence)
        augmented["espr:product_id"] = evidence.get("product_id")
        augmented["espr:dpp_id"] = evidence.get("dpp_id")
        augmented["espr:registry_ref"] = evidence.get("registry_ref")
        augmented["espr:carrier_type"] = evidence.get("carrier_type")
        augmented["espr:regulation_version"] = "2024/1781"
        augmented["espr:backup_copy_ref"] = evidence.get("backup_location_uri")
        return augmented
