"""Manufacturing-X evidence augmenter.

Implements :class:`EvidenceAugmenter` to stamp MX-specific fields onto
every evidence bundle produced during a Manufacturing-X tenancy.  Fields
added are prefixed ``mx:`` to avoid collisions with other packs.

No HTTP, DB, or Temporal code.
"""
from __future__ import annotations

from typing import Any

_MX_PACK_VERSION = "1.0.0"


class MxEvidenceAugmenter:
    """Augments evidence bundles with Manufacturing-X context.

    Fields added:
      - ``mx:profile_name``   — active MX-Port profile name (if provided in scope)
      - ``mx:pack_version``   — version of this manufacturing_x pack
      - ``mx:active_layers``  — list of active MX-Port layer values (if provided)
    """

    # ------------------------------------------------------------------
    # EvidenceAugmenter interface
    # ------------------------------------------------------------------

    def augment(
        self,
        evidence: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Return a copy of ``evidence`` with MX fields added.

        The original dict is not mutated.  Existing keys are never removed
        or overwritten — only new ``mx:*`` keys are inserted.

        Args:
            evidence:         Existing evidence bundle dict.
            activation_scope: Tenant/scope identifier for this augmentation.

        Returns:
            New dict with MX evidence fields added.
        """
        augmented = dict(evidence)

        # Pack version is always stamped
        augmented.setdefault("mx:pack_version", _MX_PACK_VERSION)

        # Profile name — may be present in the evidence already from a
        # graph or template step
        if "mx:profile_name" not in augmented:
            profile_name = evidence.get("profile_name") or evidence.get("mx_profile_name")
            if profile_name:
                augmented["mx:profile_name"] = str(profile_name)

        # Active layers — derive from graph layers if present
        if "mx:active_layers" not in augmented:
            layers = evidence.get("active_layers") or evidence.get("mx_layers")
            if layers is not None:
                if isinstance(layers, (list, tuple, set, frozenset)):
                    augmented["mx:active_layers"] = sorted(str(l) for l in layers)
                else:
                    augmented["mx:active_layers"] = str(layers)

        # Stamp the activation scope so auditors know which tenant triggered this
        augmented.setdefault("mx:activation_scope", activation_scope)

        return augmented
