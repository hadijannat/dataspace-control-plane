from __future__ import annotations

from dataspace_control_plane_packs._shared.provenance import PROVENANCE_KEY
from dataspace_control_plane_packs.espr_dpp.api import EsprAasTwinTemplateProvider
from dataspace_control_plane_packs.espr_dpp.core_rules.evidence import EsprEvidenceAugmenter


def test_espr_template_catalog_and_output_include_provenance() -> None:
    provider = EsprAasTwinTemplateProvider()
    descriptor = provider.templates(context={})[0]
    submodel = provider.apply_template(
        "espr_dpp_v1",
        {"product_id": "urn:product:1", "dpp_id": "dpp-1"},
        activation_scope="tenant:acme",
    )

    assert descriptor[PROVENANCE_KEY]["records"]["espr_dpp"]["activation_scope"] == "template_catalog"
    assert submodel["idShort"] == "EsprDpp"
    assert submodel[PROVENANCE_KEY]["records"]["espr_dpp"]["activation_scope"] == "tenant:acme"


def test_espr_evidence_output_includes_provenance() -> None:
    evidence = EsprEvidenceAugmenter().augment(
        {"product_id": "urn:product:1", "dpp_id": "dpp-1"},
        activation_scope="tenant:acme",
    )

    assert evidence[PROVENANCE_KEY]["records"]["espr_dpp"]["pack_version"] == "2024.1781.1"
