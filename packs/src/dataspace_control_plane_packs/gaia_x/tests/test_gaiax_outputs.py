from __future__ import annotations

from dataspace_control_plane_packs._shared.provenance import PROVENANCE_KEY
from dataspace_control_plane_packs.gaia_x.baseline.credentials import GaiaXCredentialProfileProvider
from dataspace_control_plane_packs.gaia_x.baseline.trust_anchors import GaiaXBaselineTrustAnchorOverlay


def test_gaiax_credential_payload_includes_provenance() -> None:
    payload = GaiaXCredentialProfileProvider().build_vc_payload(
        "participant",
        {
            "id": "did:web:example.com",
            "legal_name": "Acme GmbH",
            "legal_registration_number": "HRB-1",
            "headquarter_address": "HQ",
            "legal_address": "LA",
        },
        activation_scope="tenant:acme",
    )

    assert payload["credentialSubject"]["gx:legalName"] == "Acme GmbH"
    assert payload[PROVENANCE_KEY]["records"]["gaia_x"]["activation_scope"] == "tenant:acme"


def test_gaiax_baseline_trust_anchor_overlay_uses_pinned_defaults() -> None:
    overlay = GaiaXBaselineTrustAnchorOverlay()
    base_anchors = [
        {"did": "did:web:one.example"},
        {"did": "did:web:two.example"},
    ]

    assert overlay.overlay_anchors(base_anchors) == base_anchors
