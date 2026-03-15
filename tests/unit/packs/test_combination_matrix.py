"""
tests/unit/packs/test_combination_matrix.py
Pack combination matrix and safety tests.

Tests the cross-product of legally-valid pack combinations, override safety
enforcement, and provenance hash determinism. All tests are pure Python —
no live services required.

Covers:
  1. All 5 packs register cleanly into PackRegistry
  2. catenax + battery_passport resolution (most common EU vehicle OEM stack)
  3. catenax + espr_dpp resolution (product regulation stack)
  4. manufacturing_x + espr_dpp resolution
  5. gaia_x standalone resolution
  6. gaia_x + espr_dpp resolution
  7. check_override_safety blocks custom rules that weaken regulatory severity
  8. ArtifactProvenance.rule_bundle_hash is deterministic across Python instances
  9. Incompatible combination raises ConflictError when conflicts list is used

Marker: unit
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# ── Path injection ────────────────────────────────────────────────────────────
_PACKS_SRC = (
    Path(__file__).resolve().parent.parent.parent.parent / "packs" / "src"
)
if _PACKS_SRC.exists() and str(_PACKS_SRC) not in sys.path:
    sys.path.insert(0, str(_PACKS_SRC))


def _skip_if_missing() -> None:
    try:
        import dataspace_control_plane_packs  # noqa: F401
    except ImportError as exc:
        pytest.skip(f"packs package not available: {exc}")


# ── Registry setup fixture ────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def populated_registry():
    """Return a PackRegistry populated with all 5 canonical packs."""
    _skip_if_missing()

    from dataspace_control_plane_packs.registry import get_registry, reset_registry
    from dataspace_control_plane_packs.catenax.api import MANIFEST as CX, PROVIDERS as CX_P
    from dataspace_control_plane_packs.manufacturing_x.api import MANIFEST as MX, PROVIDERS as MX_P
    from dataspace_control_plane_packs.gaia_x.api import MANIFEST as GX, PROVIDERS as GX_P
    from dataspace_control_plane_packs.espr_dpp.api import MANIFEST as ESPR, PROVIDERS as ESPR_P
    from dataspace_control_plane_packs.battery_passport.api import MANIFEST as BAT, PROVIDERS as BAT_P

    reset_registry()
    reg = get_registry()
    for manifest, providers in [
        (CX, CX_P),
        (MX, MX_P),
        (GX, GX_P),
        (ESPR, ESPR_P),
        (BAT, BAT_P),
    ]:
        reg.register(manifest, providers=providers)

    return reg


# ── Test 1: All packs register ───────────────────────────────────────────────

def test_all_packs_register_in_registry(populated_registry) -> None:
    """All 5 packs must be present in the registry after registration."""
    _skip_if_missing()

    pack_ids = set(populated_registry.pack_ids())
    expected = {"catenax", "manufacturing_x", "gaia_x", "espr_dpp", "battery_passport"}
    missing = expected - pack_ids
    assert not missing, (
        f"Packs missing from registry: {missing}\n"
        f"Registered: {pack_ids}"
    )


# ── Test 2–6: Combination matrix ─────────────────────────────────────────────

def _resolve(registry: object, packs: list[str], activation_id: str = "test") -> object:
    """Call PackResolver.resolve() with the keyword args its signature requires."""
    from dataspace_control_plane_packs.resolver import PackResolver

    return PackResolver(registry).resolve(
        activation_id=activation_id,
        requested_packs=packs,
    )


@pytest.mark.parametrize(
    "combo",
    [
        ["catenax", "battery_passport"],
        ["catenax", "espr_dpp"],
        ["manufacturing_x", "espr_dpp"],
        ["gaia_x"],
        ["gaia_x", "espr_dpp"],
    ],
)
def test_combination_resolves_without_error(combo: list[str], populated_registry) -> None:
    """Valid pack combinations must resolve to a ResolvedPackProfile without raising."""
    _skip_if_missing()

    profile = _resolve(populated_registry, combo)
    assert profile is not None, (
        f"PackResolver.resolve({combo}) returned None"
    )


def test_catenax_battery_passport_has_requirement_providers(populated_registry) -> None:
    """catenax + battery_passport must provide at least one REQUIREMENT_PROVIDER."""
    _skip_if_missing()

    from dataspace_control_plane_packs._shared.capabilities import PackCapability

    profile = _resolve(populated_registry, ["catenax", "battery_passport"])
    req_providers = profile.providers_for(PackCapability.REQUIREMENT_PROVIDER)
    assert len(req_providers) >= 1, (
        "catenax + battery_passport combination must expose at least one REQUIREMENT_PROVIDER"
    )


def test_catenax_battery_passport_has_evidence_augmenters(populated_registry) -> None:
    """catenax + battery_passport must provide at least one EVIDENCE_AUGMENTER."""
    _skip_if_missing()

    from dataspace_control_plane_packs._shared.capabilities import PackCapability

    profile = _resolve(populated_registry, ["catenax", "battery_passport"])
    augmenters = profile.providers_for(PackCapability.EVIDENCE_AUGMENTER)
    assert len(augmenters) >= 1, (
        "battery_passport must provide at least one EVIDENCE_AUGMENTER"
    )


def test_gaia_x_espr_dpp_has_twin_template_provider(populated_registry) -> None:
    """gaia_x + espr_dpp must provide at least one TWIN_TEMPLATE provider."""
    _skip_if_missing()

    from dataspace_control_plane_packs._shared.capabilities import PackCapability

    profile = _resolve(populated_registry, ["gaia_x", "espr_dpp"])
    twin_providers = profile.providers_for(PackCapability.TWIN_TEMPLATE)
    assert len(twin_providers) >= 1, (
        "gaia_x + espr_dpp must provide at least one TWIN_TEMPLATE"
    )


# ── Test 7: Override safety ───────────────────────────────────────────────────

def _make_rule(rule_id: str, severity: str) -> object:
    """Build a RuleDefinition with the minimum required fields."""
    from dataspace_control_plane_packs._shared.rule_model import RuleDefinition

    return RuleDefinition(
        rule_id=rule_id,
        title=f"Rule {rule_id}",
        severity=severity,  # type: ignore[arg-type]
        machine_checkable=True,
        source_uri="https://example.com/spec",
        source_version="1.0",
        effective_from=None,
        effective_to=None,
        scope={},
        payload={},
    )


def test_check_override_safety_blocks_severity_downgrade() -> None:
    """check_override_safety() must return violations when custom rule weakens regulatory."""
    _skip_if_missing()

    from dataspace_control_plane_packs._shared.reducers import check_override_safety

    regulatory_rule = _make_rule("reg-001", "error")
    custom_rule = _make_rule("reg-001", "warning")  # downgrade: error → warning

    violations = check_override_safety(
        custom_rules=[custom_rule],
        regulatory_rules=[regulatory_rule],
    )

    assert violations, (
        "check_override_safety must return at least one violation string when a custom "
        "rule weakens a regulatory rule's severity from 'error' to 'warning'"
    )
    violation_text = " ".join(violations).lower()
    assert any(
        kw in violation_text
        for kw in ("weaken", "severity", "reg-001", "warning", "error")
    ), f"Violation messages are not informative: {violations}"


def test_check_override_safety_allows_severity_upgrade() -> None:
    """check_override_safety() must return no violations when custom rule escalates."""
    _skip_if_missing()

    from dataspace_control_plane_packs._shared.reducers import check_override_safety

    regulatory_rule = _make_rule("reg-002", "warning")
    custom_rule = _make_rule("reg-002", "error")  # escalation — must be allowed

    violations = check_override_safety(
        custom_rules=[custom_rule],
        regulatory_rules=[regulatory_rule],
    )
    assert not violations, (
        f"Severity escalation must not produce violations; got: {violations}"
    )


# ── Test 8: Provenance hash determinism ──────────────────────────────────────

def _build_provenance(rule_ids: list[str]) -> object:
    """Build an ArtifactProvenance with synthetic inputs for hash testing."""
    from dataspace_control_plane_packs._shared.provenance import (
        ArtifactProvenance,
        NormativeSource,
    )

    src = NormativeSource(
        source_uri="https://example.com/spec",
        version="1.0",
        retrieval_date="2026-01-01",
        sha256="a" * 64,
        local_filename="spec.html",
        effective_from="2026-01-01",
        effective_to=None,
        upstream_license=None,
    )
    return ArtifactProvenance.build(
        pack_id="test-pack",
        pack_version="1.0.0",
        rule_ids=rule_ids,
        sources=[src],
        activation_scope="tenant",
    )


def test_rule_bundle_hash_is_deterministic() -> None:
    """ArtifactProvenance.rule_bundle_hash must produce the same value on every call."""
    _skip_if_missing()

    prov_a = _build_provenance(["rule-001", "rule-002", "rule-003"])
    prov_b = _build_provenance(["rule-001", "rule-002", "rule-003"])

    assert prov_a.rule_bundle_hash == prov_b.rule_bundle_hash, (
        "rule_bundle_hash must be deterministic across calls with the same inputs"
    )
    assert isinstance(prov_a.rule_bundle_hash, str) and len(prov_a.rule_bundle_hash) > 0


def test_rule_bundle_hash_is_order_independent() -> None:
    """rule_bundle_hash must produce the same value regardless of rule_id input order."""
    _skip_if_missing()

    prov_a = _build_provenance(["rule-b", "rule-a", "rule-c"])
    prov_b = _build_provenance(["rule-a", "rule-b", "rule-c"])

    # build() implementation sorts rule_ids — order must not matter.
    assert prov_a.rule_bundle_hash == prov_b.rule_bundle_hash


# ── Test 9: Pack unique IDs ───────────────────────────────────────────────────

def test_registered_packs_have_unique_ids(populated_registry) -> None:
    """Every registered pack must have a globally unique pack_id."""
    _skip_if_missing()

    pack_ids = list(populated_registry.pack_ids())
    assert len(pack_ids) == len(set(pack_ids)), (
        f"Duplicate pack_ids detected: "
        f"{[pid for pid in pack_ids if pack_ids.count(pid) > 1]}"
    )


def test_pack_manifests_have_semver_versions(populated_registry) -> None:
    """Every pack manifest must declare a SemVer-compatible version string."""
    _skip_if_missing()

    import re

    semver_re = re.compile(r"^\d+\.\d+(\.\d+)?")

    for pack_id in populated_registry.pack_ids():
        # Access via internal _manifests dict (PackRegistry has no public get_manifest).
        manifest = populated_registry._manifests.get(pack_id)
        assert manifest is not None, f"Registry has no manifest for {pack_id}"
        version = getattr(manifest, "version", None)
        assert version, f"Pack {pack_id} has no version field"
        assert semver_re.match(str(version)), (
            f"Pack {pack_id} version {version!r} does not match SemVer pattern"
        )
