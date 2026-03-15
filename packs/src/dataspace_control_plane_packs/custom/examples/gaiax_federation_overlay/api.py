"""Gaia-X federation overlay — example implementation.

This module demonstrates the ``TrustAnchorOverlayProvider`` capability.
A Gaia-X federation selects a subset of the global Gaia-X trust anchors
that are recognised within its scope. Anchors without a ``federation_id``
field are always included (they are global anchors valid in all federations).

This is an EXAMPLE pack. It is not for production use. Copy to
``custom/org_packs/<your_federation_id>/`` and update the FEDERATION_ID and
manifest before activating in a real deployment.
"""
from __future__ import annotations

from typing import Any

from ...._shared.manifest import PackManifest, PackCapabilityDecl, _minimal_manifest
from ...._shared.capabilities import PackCapability

# ---------------------------------------------------------------------------
# Federation identity
# ---------------------------------------------------------------------------

FEDERATION_ID = "example_eu_cloud"
"""Identifier matching the ``federation_id`` field on Gaia-X trust anchors.

Anchors tagged with this federation_id are included in the overlay set.
Anchors with no federation_id are global and are always included.
"""


# ---------------------------------------------------------------------------
# TrustAnchorOverlayProvider
# ---------------------------------------------------------------------------

class ExampleFederationTrustAnchorOverlay:
    """TrustAnchorOverlayProvider for the example EU-cloud Gaia-X federation.

    Filters the base Gaia-X trust anchor set down to:
    - Anchors whose ``federation_id`` matches ``FEDERATION_ID``
    - Anchors whose ``federation_id`` is ``None`` or absent (global anchors)

    Anchors belonging to other federations are excluded so that only
    trust relationships relevant to this federation remain active.

    This is a reference example — not for production use.
    """

    def overlay_anchors(
        self, base_anchors: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Filter ``base_anchors`` to this federation's scope.

        Args:
            base_anchors: The full list of Gaia-X trust anchor dicts provided
                by the base ``gaia_x`` pack. Each dict may carry a
                ``federation_id`` string field.

        Returns:
            A filtered list containing only anchors that belong to
            ``FEDERATION_ID`` or that carry no federation restriction.
        """
        filtered = []
        for anchor in base_anchors:
            anchor_federation = anchor.get("federation_id")
            if anchor_federation is None or anchor_federation == FEDERATION_ID:
                filtered.append(anchor)
        return filtered


# ---------------------------------------------------------------------------
# Pack manifest and provider registry
# ---------------------------------------------------------------------------

MANIFEST: PackManifest = _minimal_manifest(
    pack_id="example_eu_cloud_federation",
    pack_kind="custom",
    version="1.0.0",
    display_name="Example EU Cloud Federation Overlay",
    description=(
        "Reference example of a Gaia-X federation overlay pack. "
        "Not for production use."
    ),
    capabilities=[
        PackCapabilityDecl(
            capability=PackCapability.TRUST_ANCHOR_OVERLAY,
            interface_class=(
                "dataspace_control_plane_packs.custom.examples"
                ".gaiax_federation_overlay.api.ExampleFederationTrustAnchorOverlay"
            ),
        )
    ],
)

PROVIDERS: dict[PackCapability, Any] = {
    PackCapability.TRUST_ANCHOR_OVERLAY: ExampleFederationTrustAnchorOverlay(),
}
