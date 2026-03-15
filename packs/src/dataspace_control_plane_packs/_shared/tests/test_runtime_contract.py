from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from dataspace_control_plane_packs._shared.errors import NormativeSourceError, PackVersionError
from dataspace_control_plane_packs._shared.capabilities import PackCapability
from dataspace_control_plane_packs._shared.manifest import PackManifest
from dataspace_control_plane_packs._shared.provenance import NormativeSource, validate_manifest_sources
from dataspace_control_plane_packs._shared.reducers import reduce_defaults, reduce_validation
from dataspace_control_plane_packs._shared.rule_model import RuleViolation, ValidationResult
from dataspace_control_plane_packs.activation import ActivationRequest, PackActivationManager
from dataspace_control_plane_packs.loader import discover_pack_modules, load_all_builtin_packs
from dataspace_control_plane_packs.registry import PackRegistry
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


def test_reduce_defaults_applies_custom_last() -> None:
    merged = reduce_defaults(
        [
            ("ecosystem", {"policy_mode": "ecosystem"}),
            ("regulation", {"policy_mode": "regulation"}),
            ("custom", {"policy_mode": "custom"}),
        ]
    )
    assert merged["policy_mode"] == "custom"


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
