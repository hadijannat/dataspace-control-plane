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
    assert evidence[PROVENANCE_KEY]["records"]["battery_passport"]["pack_version"] == "2023.1542.1"


def test_battery_linkage_requires_successor_in_repurposed_states() -> None:
    result = validate_linkage({"battery_id": "BAT-1"}, "repurposed")
    assert result.passed is False


# ---------------------------------------------------------------------------
# BatteryLifecycleProvider — validate_transition coverage
# ---------------------------------------------------------------------------

def test_battery_lifecycle_valid_transition_passes() -> None:
    lifecycle = BatteryLifecycleProvider()
    result = lifecycle.validate_transition(
        "active", "repurposed", context={"battery_id": "BAT-2"}
    )
    assert result.passed is True
    assert result.violations == []


def test_battery_lifecycle_invalid_transition_produces_error() -> None:
    lifecycle = BatteryLifecycleProvider()
    # active → recycled_ceased is not a direct allowed transition
    result = lifecycle.validate_transition(
        "active", "recycled_ceased", context={"battery_id": "BAT-3"}
    )
    assert result.passed is False
    assert any(v.rule_id == "battery:lifecycle-invalid-transition" for v in result.violations)


def test_battery_lifecycle_terminal_state_blocks_any_transition() -> None:
    lifecycle = BatteryLifecycleProvider()
    result = lifecycle.validate_transition(
        "recycled_ceased", "active", context={"battery_id": "BAT-4"}
    )
    assert result.passed is False
    assert any(v.rule_id == "battery:lifecycle-terminal-state" for v in result.violations)


def test_battery_lifecycle_transitions_list_is_non_empty() -> None:
    lifecycle = BatteryLifecycleProvider()
    transitions = lifecycle.transitions()
    assert len(transitions) > 0
    # Every transition entry must have the expected keys
    for t in transitions:
        assert "from" in t and "to" in t and "trigger" in t


def test_battery_lifecycle_waste_to_recycled_ceased_is_allowed() -> None:
    lifecycle = BatteryLifecycleProvider()
    result = lifecycle.validate_transition(
        "waste", "recycled_ceased", context={"battery_id": "BAT-5"}
    )
    assert result.passed is True
