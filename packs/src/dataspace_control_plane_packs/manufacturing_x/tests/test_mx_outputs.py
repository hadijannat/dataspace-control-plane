from __future__ import annotations

from dataspace_control_plane_packs._shared.provenance import PROVENANCE_KEY
from dataspace_control_plane_packs.manufacturing_x.aas_dpp4o_bridge import MxTwinTemplateProvider
from dataspace_control_plane_packs.manufacturing_x.evidence import MxEvidenceAugmenter


def test_mx_templates_and_evidence_include_provenance() -> None:
    provider = MxTwinTemplateProvider()
    descriptor = provider.templates(context={})[0]
    submodel = provider.apply_template(
        "mx:capability-declaration",
        {
            "id": "urn:mx:asset:1",
            "profile_name": "hercules",
            "layers": ["discovery", "gate"],
            "protocols": ["dsp", "aas-rest"],
        },
        activation_scope="tenant:acme",
    )
    evidence = MxEvidenceAugmenter().augment(
        {"profile_name": "hercules", "active_layers": ["discovery", "gate"]},
        activation_scope="tenant:acme",
    )

    assert descriptor[PROVENANCE_KEY]["records"]["manufacturing_x"]["activation_scope"] == "template_catalog"
    assert submodel[PROVENANCE_KEY]["records"]["manufacturing_x"]["activation_scope"] == "tenant:acme"
    assert evidence[PROVENANCE_KEY]["records"]["manufacturing_x"]["pack_version"] == "1.0.0"


def test_mx_outputs_do_not_assume_catenax_or_gaiax_namespaces() -> None:
    submodel = MxTwinTemplateProvider().apply_template(
        "mx:capability-declaration",
        {"id": "urn:mx:asset:1"},
        activation_scope="tenant:acme",
    )

    assert not any(key.startswith("cx:") for key in submodel)
    assert not any(key.startswith("gx:") for key in submodel)
