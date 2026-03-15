from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from dataspace_control_plane_packs._shared.errors import (
    NormativeSourceError,
    PackActivationError,
    PackConflictError,
    PackNotFoundError,
    PackValidationError,
    PackVersionError,
)
from dataspace_control_plane_packs._shared.capabilities import PackCapability
from dataspace_control_plane_packs._shared.manifest import PackManifest, _minimal_manifest, PackCapabilityDecl
from dataspace_control_plane_packs._shared.provenance import (
    PROVENANCE_KEY,
    NormativeSource,
    attach_pack_provenance,
    require_pack_provenance,
    validate_manifest_sources,
)
from dataspace_control_plane_packs._shared.reducers import (
    check_override_safety,
    reduce_defaults,
    reduce_evidence,
    reduce_identifier_schemes,
    reduce_policy_compiler,
    reduce_validation,
)
from dataspace_control_plane_packs._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult
from dataspace_control_plane_packs.activation import ActivationRequest, PackActivationManager
from dataspace_control_plane_packs.loader import discover_pack_modules, load_all_builtin_packs, load_pack
from dataspace_control_plane_packs.registry import PackRegistry, get_registry, reset_registry
from dataspace_control_plane_packs.resolver import PackResolver


@dataclass
class FakeRequirementProvider:
    violations: list[RuleViolation]

    def requirements(self, *, context: dict, on=None) -> list:  # pragma: no cover - unused in tests
        return []

    def validate(self, subject: dict, *, context: dict, on=None) -> ValidationResult:
        result = ValidationResult(subject_id=context.get("subject_id", "subject-1"))
        for violation in self.violations:
            result.add(violation)
        return result


def test_reduce_defaults_custom_cannot_override_regulated_key() -> None:
    """reduce_defaults must raise if a custom pack tries to override a regulation key.

    The architectural invariant (from README and check_override_safety) is that
    custom packs may add new keys or tighten rules, but must never silently replace
    a default established by a regulation pack.
    """
    with pytest.raises(ValueError, match="regulation"):
        reduce_defaults(
            [
                ("ecosystem", {"policy_mode": "ecosystem"}),
                ("regulation", {"policy_mode": "regulation"}),
                ("custom", {"policy_mode": "custom"}),
            ]
        )


def test_reduce_defaults_custom_can_add_new_keys_not_in_regulation() -> None:
    """Custom packs may introduce keys that no regulation pack declared."""
    merged = reduce_defaults(
        [
            ("ecosystem", {"policy_mode": "ecosystem"}),
            ("regulation", {"audit_required": True}),
            ("custom", {"extra_flag": "custom_only"}),
        ]
    )
    assert merged["policy_mode"] == "ecosystem"
    assert merged["audit_required"] is True
    assert merged["extra_flag"] == "custom_only"


def test_reduce_validation_short_circuits_on_first_error() -> None:
    providers = [
        FakeRequirementProvider(
            [
                RuleViolation(rule_id="warn-1", severity="warning", message="warn"),
                RuleViolation(rule_id="err-1", severity="error", message="stop"),
                RuleViolation(rule_id="err-2", severity="error", message="not reached"),
            ]
        ),
        FakeRequirementProvider(
            [RuleViolation(rule_id="err-3", severity="error", message="later")]
        ),
    ]

    result = reduce_validation(
        providers,
        {},
        context={"subject_id": "subject-1"},
        short_circuit_on_error=True,
    )

    assert [violation.rule_id for violation in result.violations] == ["warn-1", "err-1"]


def test_discover_pack_modules_includes_custom_examples() -> None:
    modules = discover_pack_modules()
    assert "dataspace_control_plane_packs.custom.examples.enterprise_policy_overlay.api" in modules
    assert "dataspace_control_plane_packs.custom.examples.gaiax_federation_overlay.api" in modules


def test_load_all_builtin_packs_registers_multiple_identifier_schemes() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)

    providers = registry.providers_for_pack("catenax", PackCapability.IDENTIFIER_SCHEME)
    provider_names = {type(provider).__name__ for provider in providers}
    assert provider_names == {"BpnlSchemeProvider", "BpnsSchemeProvider", "BpnaSchemeProvider"}


def test_validate_manifest_sources_rejects_bad_checksum(tmp_path: Path) -> None:
    source_dir = tmp_path / "vocab" / "pinned"
    source_dir.mkdir(parents=True)
    source_path = source_dir / "fixture.txt"
    source_path.write_text("fixture")

    manifest = PackManifest(
        pack_id="tmp-pack",
        pack_kind="custom",
        version="1.0.0",
        display_name="tmp",
        description="tmp",
        compatibility={},
        activation_scope="tenant",
        dependencies=(),
        conflicts=(),
        capabilities=(),
        normative_sources=(
            NormativeSource(
                source_uri="https://example.com/spec",
                version="1.0",
                retrieval_date="2026-03-15",
                sha256="deadbeef",
                local_filename="vocab/pinned/fixture.txt",
            ),
        ),
        default_priority=100,
        root_dir=str(tmp_path),
    )

    with pytest.raises(NormativeSourceError):
        validate_manifest_sources(manifest)


def test_activation_cache_invalidates_when_options_change() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    manager = PackActivationManager(registry)

    first = manager.activate(
        ActivationRequest(
            scope_kind="tenant",
            scope_id="tenant-acme",
            requested_packs=["catenax"],
            pack_options={"profile": "baseline"},
            compatibility_context={"core_version": "0.1.0"},
        )
    )
    second = manager.activate(
        ActivationRequest(
            scope_kind="tenant",
            scope_id="tenant-acme",
            requested_packs=["catenax"],
            pack_options={"profile": "strict"},
            compatibility_context={"core_version": "0.1.0"},
        )
    )

    assert first is not second
    assert first.metadata["pack_options"] == {"profile": "baseline"}
    assert second.metadata["pack_options"] == {"profile": "strict"}


def test_resolver_enforces_manifest_compatibility_when_metadata_is_supplied() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)

    with pytest.raises(PackVersionError):
        PackResolver(registry).resolve(
            activation_id="tenant:acme",
            requested_packs=["catenax"],
            metadata={"core_version": "0.0.1"},
        )


# ---------------------------------------------------------------------------
# Registry — boundary conditions
# ---------------------------------------------------------------------------

def test_registry_manifest_raises_not_found_for_unknown_pack() -> None:
    registry = PackRegistry()
    with pytest.raises(PackNotFoundError):
        registry.manifest("does_not_exist")


def test_registry_has_pack_returns_false_before_registration() -> None:
    registry = PackRegistry()
    assert registry.has_pack("catenax") is False


def test_registry_duplicate_registration_overwrites_silently(caplog) -> None:
    import logging

    registry = PackRegistry()
    manifest = _minimal_manifest("dup-pack", "ecosystem", "1.0.0", "Dup", "Duplicate pack test")

    with caplog.at_level(logging.WARNING):
        registry.register(manifest)
        registry.register(manifest)

    assert any("already registered" in record.message for record in caplog.records)
    assert registry.has_pack("dup-pack")


def test_registry_provider_for_undeclared_capability_raises_validation_error() -> None:
    registry = PackRegistry()
    manifest = _minimal_manifest(
        "bad-pack",
        "ecosystem",
        "1.0.0",
        "Bad",
        "No declared capabilities",
    )
    with pytest.raises(PackValidationError):
        registry.register(
            manifest,
            providers={PackCapability.REQUIREMENT_PROVIDER: object()},
        )


def test_registry_providers_for_pack_returns_empty_for_unknown_capability() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    result = registry.providers_for_pack("catenax", PackCapability.LIFECYCLE_MODEL)
    assert result == []


def test_registry_provider_for_pack_returns_none_when_no_instance() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    result = registry.provider_for_pack("catenax", PackCapability.LIFECYCLE_MODEL)
    assert result is None


def test_registry_global_singleton_resets() -> None:
    reset_registry()
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2
    reset_registry()
    r3 = get_registry()
    assert r3 is not r1


# ---------------------------------------------------------------------------
# Loader — error paths
# ---------------------------------------------------------------------------

def test_load_pack_returns_false_for_nonexistent_module() -> None:
    registry = PackRegistry()
    result = load_pack("dataspace_control_plane_packs.no_such_module_xyz", registry)
    assert result is False


def test_load_pack_returns_false_when_manifest_attribute_missing(monkeypatch, tmp_path) -> None:
    import sys
    import types

    fake_module = types.ModuleType("fake_pack_no_manifest")
    # No MANIFEST attribute — simulates a broken pack
    sys.modules["fake_pack_no_manifest"] = fake_module
    try:
        registry = PackRegistry()
        result = load_pack("fake_pack_no_manifest", registry)
        assert result is False
    finally:
        del sys.modules["fake_pack_no_manifest"]


def test_discover_pack_modules_has_no_duplicates() -> None:
    modules = discover_pack_modules()
    assert len(modules) == len(set(modules)), "discover_pack_modules returned duplicate entries"


def test_discover_pack_modules_includes_all_builtin_packs() -> None:
    from dataspace_control_plane_packs.loader import BUILTIN_PACKS

    modules = discover_pack_modules()
    for expected in BUILTIN_PACKS:
        assert expected in modules


# ---------------------------------------------------------------------------
# Resolver — error paths and boundary conditions
# ---------------------------------------------------------------------------

def test_resolver_raises_not_found_for_unknown_pack() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)

    with pytest.raises(PackNotFoundError):
        PackResolver(registry).resolve(
            activation_id="tenant:test",
            requested_packs=["unknown_pack_xyz"],
        )


def test_resolver_raises_conflict_error_for_declared_conflict(monkeypatch) -> None:
    """Two packs that declare each other as conflicts must not resolve together."""
    from dataspace_control_plane_packs._shared.manifest import PackManifest

    registry = PackRegistry()
    load_all_builtin_packs(registry)

    # Build two minimal packs that conflict with each other
    manifest_a = PackManifest(
        pack_id="conflict_a",
        pack_kind="ecosystem",
        version="1.0.0",
        display_name="A",
        description="A",
        compatibility={},
        activation_scope="tenant",
        dependencies=(),
        conflicts=("conflict_b",),
        capabilities=(),
        normative_sources=(),
        default_priority=100,
        root_dir=".",
    )
    manifest_b = PackManifest(
        pack_id="conflict_b",
        pack_kind="ecosystem",
        version="1.0.0",
        display_name="B",
        description="B",
        compatibility={},
        activation_scope="tenant",
        dependencies=(),
        conflicts=(),
        capabilities=(),
        normative_sources=(),
        default_priority=100,
        root_dir=".",
    )
    registry.register(manifest_a)
    registry.register(manifest_b)

    with pytest.raises(PackConflictError):
        PackResolver(registry).resolve(
            activation_id="tenant:test",
            requested_packs=["conflict_a", "conflict_b"],
        )


def test_resolver_empty_requested_packs_returns_empty_profile() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    profile = PackResolver(registry).resolve(
        activation_id="tenant:test",
        requested_packs=[],
    )
    assert profile.pack_ids() == []
    assert profile.providers_for(PackCapability.REQUIREMENT_PROVIDER) == []


def test_resolved_profile_has_pack_returns_correct_boolean() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    profile = PackResolver(registry).resolve(
        activation_id="tenant:test",
        requested_packs=["catenax"],
        metadata={"core_version": "0.1.0"},
    )
    assert profile.has_pack("catenax") is True
    assert profile.has_pack("manufacturing_x") is False


# ---------------------------------------------------------------------------
# Activation — cache hit, deactivate, get_profile, error wrapping
# ---------------------------------------------------------------------------

def test_activation_cache_returns_same_object_for_identical_request() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    manager = PackActivationManager(registry)

    request = ActivationRequest(
        scope_kind="tenant",
        scope_id="tenant-cache-test",
        requested_packs=["catenax"],
        pack_options={},
        compatibility_context={"core_version": "0.1.0"},
    )
    first = manager.activate(request)
    second = manager.activate(request)
    assert first is second


def test_activation_deactivate_clears_cache() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    manager = PackActivationManager(registry)

    request = ActivationRequest(
        scope_kind="tenant",
        scope_id="tenant-deactivate-test",
        requested_packs=["catenax"],
        pack_options={},
        compatibility_context={"core_version": "0.1.0"},
    )
    first = manager.activate(request)
    manager.deactivate("tenant", "tenant-deactivate-test")
    second = manager.activate(request)
    # After deactivation a new profile object is produced
    assert first is not second


def test_activation_get_profile_returns_none_before_activation() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    manager = PackActivationManager(registry)
    assert manager.get_profile("tenant", "never-activated") is None


def test_activation_get_profile_returns_profile_after_activation() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    manager = PackActivationManager(registry)

    manager.activate(
        ActivationRequest(
            scope_kind="tenant",
            scope_id="tenant-get-profile",
            requested_packs=["catenax"],
            pack_options={},
            compatibility_context={"core_version": "0.1.0"},
        )
    )
    profile = manager.get_profile("tenant", "tenant-get-profile")
    assert profile is not None
    assert profile.has_pack("catenax")


def test_activation_wraps_resolution_failure_as_pack_activation_error() -> None:
    registry = PackRegistry()
    load_all_builtin_packs(registry)
    manager = PackActivationManager(registry)

    with pytest.raises(PackActivationError):
        manager.activate(
            ActivationRequest(
                scope_kind="tenant",
                scope_id="tenant-bad",
                requested_packs=["nonexistent_pack_xyz"],
                pack_options={},
                compatibility_context={},
            )
        )


# ---------------------------------------------------------------------------
# Reducers — full coverage
# ---------------------------------------------------------------------------

def test_reduce_defaults_shared_is_overridden_by_ecosystem() -> None:
    merged = reduce_defaults(
        [
            ("shared", {"a": "shared", "b": "shared"}),
            ("ecosystem", {"a": "ecosystem"}),
        ]
    )
    assert merged["a"] == "ecosystem"
    assert merged["b"] == "shared"


def test_reduce_defaults_full_priority_chain_raises_on_custom_regulation_conflict() -> None:
    """The full chain base→ecosystem→regulation→custom raises when custom overrides a regulated key."""
    with pytest.raises(ValueError, match="regulation"):
        reduce_defaults(
            [
                ("base", {"key": "base"}),
                ("ecosystem", {"key": "ecosystem"}),
                ("regulation", {"key": "regulation"}),
                ("custom", {"key": "custom"}),
            ]
        )


def test_reduce_defaults_full_priority_chain_non_conflicting() -> None:
    """Full chain where each kind owns distinct keys resolves without error."""
    merged = reduce_defaults(
        [
            ("base", {"base_key": "base"}),
            ("ecosystem", {"eco_key": "ecosystem"}),
            ("regulation", {"reg_key": "regulation"}),
            ("custom", {"custom_key": "custom"}),
        ]
    )
    assert merged["base_key"] == "base"
    assert merged["eco_key"] == "ecosystem"
    assert merged["reg_key"] == "regulation"
    assert merged["custom_key"] == "custom"


def test_reduce_defaults_empty_input_returns_empty_dict() -> None:
    assert reduce_defaults([]) == {}


def test_reduce_validation_accumulates_all_warnings_without_short_circuit() -> None:
    providers = [
        FakeRequirementProvider(
            [RuleViolation(rule_id="w1", severity="warning", message="w")]
        ),
        FakeRequirementProvider(
            [RuleViolation(rule_id="w2", severity="warning", message="w")]
        ),
    ]
    result = reduce_validation(
        providers, {}, context={"subject_id": "s"}, short_circuit_on_error=False
    )
    assert {v.rule_id for v in result.violations} == {"w1", "w2"}


def test_reduce_validation_empty_providers_returns_passed() -> None:
    result = reduce_validation([], {}, context={"subject_id": "s"})
    assert result.passed is True


def test_reduce_evidence_preserves_existing_fields_across_augmenters() -> None:
    from dataspace_control_plane_packs._shared.interfaces import EvidenceAugmenter

    class AddFieldAugmenter(EvidenceAugmenter):
        def augment(self, evidence: dict, *, activation_scope: str) -> dict:
            return {**evidence, "new_field": "added"}

    result = reduce_evidence(
        [AddFieldAugmenter()],
        {"original": "value"},
        activation_scope="tenant:test",
    )
    assert result["original"] == "value"
    assert result["new_field"] == "added"


def test_reduce_evidence_later_augmenter_cannot_drop_earlier_fields() -> None:
    from dataspace_control_plane_packs._shared.interfaces import EvidenceAugmenter

    class DroppingAugmenter(EvidenceAugmenter):
        """Simulates a buggy augmenter that drops an existing field."""
        def augment(self, evidence: dict, *, activation_scope: str) -> dict:
            # Only returns new field, omits "original"
            return {"injected": "yes"}

    result = reduce_evidence(
        [DroppingAugmenter()],
        {"original": "kept"},
        activation_scope="tenant:test",
    )
    # The reducer safety net must restore the dropped field
    assert result["original"] == "kept"
    assert result["injected"] == "yes"


def test_reduce_identifier_schemes_raises_on_duplicate_scheme() -> None:
    from dataspace_control_plane_packs._shared.interfaces import IdentifierSchemeProvider

    class FakeScheme(IdentifierSchemeProvider):
        def __init__(self, sid: str) -> None:
            self._sid = sid

        @property
        def scheme_id(self) -> str:
            return self._sid

        def validate(self, identifier: str) -> bool:
            return True

        def normalize(self, identifier: str) -> str:
            return identifier

    with pytest.raises(ValueError, match="scheme_id"):
        reduce_identifier_schemes([FakeScheme("bpnl"), FakeScheme("bpnl")])


def test_reduce_policy_compiler_raises_for_unknown_dialect() -> None:
    with pytest.raises(ValueError, match="No active pack"):
        reduce_policy_compiler([], {}, target_dialect="odrl:nonexistent", activation_scope="tenant:x")


def test_check_override_safety_detects_weakening_rule() -> None:
    import datetime
    reg_rule = RuleDefinition(
        rule_id="reg:strict",
        title="Strict",
        severity="error",
        machine_checkable=True,
        source_uri="https://example.com/reg",
        source_version="1.0",
        effective_from=None,
        effective_to=None,
        scope={},
        payload={},
    )
    custom_rule = RuleDefinition(
        rule_id="reg:strict",
        title="Weakened",
        severity="warning",  # weaker than "error"
        machine_checkable=True,
        source_uri="https://example.com/reg",
        source_version="1.0",
        effective_from=None,
        effective_to=None,
        scope={},
        payload={},
    )
    violations = check_override_safety(
        custom_rules=[custom_rule], regulatory_rules=[reg_rule]
    )
    assert len(violations) == 1
    assert "weakens" in violations[0]


def test_check_override_safety_allows_stricter_custom_rule() -> None:
    import datetime
    reg_rule = RuleDefinition(
        rule_id="reg:base",
        title="Base",
        severity="warning",
        machine_checkable=True,
        source_uri="https://example.com/reg",
        source_version="1.0",
        effective_from=None,
        effective_to=None,
        scope={},
        payload={},
    )
    custom_rule = RuleDefinition(
        rule_id="reg:base",
        title="Stricter",
        severity="error",  # stricter
        machine_checkable=True,
        source_uri="https://example.com/reg",
        source_version="1.0",
        effective_from=None,
        effective_to=None,
        scope={},
        payload={},
    )
    violations = check_override_safety(
        custom_rules=[custom_rule], regulatory_rules=[reg_rule]
    )
    assert violations == []


# ---------------------------------------------------------------------------
# Provenance — require_pack_provenance, attach_pack_provenance merging,
#              source path enforcement
# ---------------------------------------------------------------------------

def test_require_pack_provenance_raises_when_key_is_absent() -> None:
    from dataspace_control_plane_packs._shared.errors import PackProvenanceError

    with pytest.raises(PackProvenanceError):
        require_pack_provenance({"no_provenance": True})


def test_require_pack_provenance_raises_when_records_are_empty() -> None:
    from dataspace_control_plane_packs._shared.errors import PackProvenanceError

    with pytest.raises(PackProvenanceError):
        require_pack_provenance({PROVENANCE_KEY: {"records": {}}})


def test_require_pack_provenance_passes_for_valid_artifact() -> None:
    artifact = attach_pack_provenance(
        {"data": 1},
        pack_id="test_pack",
        pack_version="1.0.0",
        sources=[],
        rule_ids=["test:rule"],
        activation_scope="tenant:x",
    )
    require_pack_provenance(artifact)  # must not raise


def test_attach_pack_provenance_merges_multiple_packs() -> None:
    artifact = attach_pack_provenance(
        {},
        pack_id="pack_a",
        pack_version="1.0.0",
        sources=[],
        rule_ids=["a:rule"],
        activation_scope="tenant:x",
    )
    artifact = attach_pack_provenance(
        artifact,
        pack_id="pack_b",
        pack_version="2.0.0",
        sources=[],
        rule_ids=["b:rule"],
        activation_scope="tenant:x",
    )
    records = artifact[PROVENANCE_KEY]["records"]
    assert "pack_a" in records
    assert "pack_b" in records
    assert records["pack_a"]["pack_version"] == "1.0.0"
    assert records["pack_b"]["pack_version"] == "2.0.0"


def test_validate_manifest_sources_rejects_source_outside_allowed_path(tmp_path: Path) -> None:
    """A source file under an arbitrary directory (not vocab/pinned/ or vendor/) must be rejected."""
    source_dir = tmp_path / "arbitrary_dir"
    source_dir.mkdir(parents=True)
    source_path = source_dir / "spec.txt"
    source_path.write_text("content")

    manifest = PackManifest(
        pack_id="bad-path-pack",
        pack_kind="custom",
        version="1.0.0",
        display_name="bad",
        description="bad",
        compatibility={},
        activation_scope="tenant",
        dependencies=(),
        conflicts=(),
        capabilities=(),
        normative_sources=(
            NormativeSource(
                source_uri="https://example.com/spec",
                version="1.0",
                retrieval_date="2026-03-15",
                sha256="anything",
                local_filename="arbitrary_dir/spec.txt",
            ),
        ),
        default_priority=100,
        root_dir=str(tmp_path),
    )

    with pytest.raises(NormativeSourceError, match="vocab/pinned"):
        validate_manifest_sources(manifest)


def test_validate_manifest_sources_rejects_missing_file(tmp_path: Path) -> None:
    source_dir = tmp_path / "vocab" / "pinned"
    source_dir.mkdir(parents=True)
    # File is NOT created

    manifest = PackManifest(
        pack_id="missing-file-pack",
        pack_kind="custom",
        version="1.0.0",
        display_name="mf",
        description="mf",
        compatibility={},
        activation_scope="tenant",
        dependencies=(),
        conflicts=(),
        capabilities=(),
        normative_sources=(
            NormativeSource(
                source_uri="https://example.com/spec",
                version="1.0",
                retrieval_date="2026-03-15",
                sha256="deadbeef",
                local_filename="vocab/pinned/missing.txt",
            ),
        ),
        default_priority=100,
        root_dir=str(tmp_path),
    )

    with pytest.raises(NormativeSourceError, match="missing"):
        validate_manifest_sources(manifest)
