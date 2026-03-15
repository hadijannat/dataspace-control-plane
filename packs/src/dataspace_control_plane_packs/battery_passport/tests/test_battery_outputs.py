from __future__ import annotations

from dataspace_control_plane_packs._shared.provenance import PROVENANCE_KEY
from dataspace_control_plane_packs.battery_passport.annex_xiii.access_matrix import build_battery_access_matrix
from dataspace_control_plane_packs.battery_passport.api import BatteryAasTwinTemplateProvider
from dataspace_control_plane_packs.battery_passport.evidence import BatteryEvidenceAugmenter
from dataspace_control_plane_packs.battery_passport.lifecycle import BatteryLifecycleProvider
from dataspace_control_plane_packs.battery_passport.linkage import validate_linkage


def test_battery_access_matrix_and_lifecycle_are_effective_dated() -> None:
    matrix = build_battery_access_matrix()
    lifecycle = BatteryLifecycleProvider()

    assert matrix.effective_from == "2027-02-18"
    assert lifecycle.states() == [
        "active",
        "repurposed",
        "remanufactured",
        "waste",
        "recycled_ceased",
    ]


def test_battery_template_and_evidence_include_provenance() -> None:
    provider = BatteryAasTwinTemplateProvider()
    descriptor = provider.templates(context={})[0]
    submodel = provider.apply_template(
        "battery_passport_v1",
        {"battery_id": "BAT-1", "manufacturer_name": "Acme"},
        activation_scope="tenant:acme",
    )
    evidence = BatteryEvidenceAugmenter().augment(
        {"battery_id": "BAT-1"},
        activation_scope="tenant:acme",
    )

    assert descriptor[PROVENANCE_KEY]["records"]["battery_passport"]["activation_scope"] == "template_catalog"
    assert submodel[PROVENANCE_KEY]["records"]["battery_passport"]["activation_scope"] == "tenant:acme"
    assert evidence[PROVENANCE_KEY]["records"]["battery_passport"]["pack_version"] == "2023.0958.1"


def test_battery_linkage_requires_successor_in_repurposed_states() -> None:
    result = validate_linkage({"battery_id": "BAT-1"}, "repurposed")
    assert result.passed is False
