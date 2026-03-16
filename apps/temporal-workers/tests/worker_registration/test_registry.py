from __future__ import annotations

import inspect

import pytest

from dataspace_control_plane_temporal_workers.bootstrap import procedure_catalog, registry


def test_all_registry_lists_exist() -> None:
    assert isinstance(registry.ONBOARDING_WORKFLOWS, list)
    assert isinstance(registry.ONBOARDING_ACTIVITIES, list)
    assert isinstance(registry.MACHINE_TRUST_WORKFLOWS, list)
    assert isinstance(registry.TWINS_WORKFLOWS, list)
    assert isinstance(registry.CONTRACTS_WORKFLOWS, list)
    assert isinstance(registry.COMPLIANCE_WORKFLOWS, list)
    assert isinstance(registry.MAINTENANCE_WORKFLOWS, list)


def test_registered_workflows_match_canonical_manifests() -> None:
    manifests = procedure_catalog.load_procedure_manifests()
    expected_workflow_types = {manifest.workflow_type for manifest in manifests.values()}
    actual_workflow_types = {
        workflow.__name__
        for workflows in (
            registry.ONBOARDING_WORKFLOWS,
            registry.MACHINE_TRUST_WORKFLOWS,
            registry.TWINS_WORKFLOWS,
            registry.CONTRACTS_WORKFLOWS,
            registry.COMPLIANCE_WORKFLOWS,
            registry.MAINTENANCE_WORKFLOWS,
        )
        for workflow in workflows
    }

    assert expected_workflow_types == actual_workflow_types


def test_zero_procedures_discovered_fails_startup(monkeypatch) -> None:
    snapshots = {
        "ONBOARDING_WORKFLOWS": list(registry.ONBOARDING_WORKFLOWS),
        "ONBOARDING_ACTIVITIES": list(registry.ONBOARDING_ACTIVITIES),
        "MACHINE_TRUST_WORKFLOWS": list(registry.MACHINE_TRUST_WORKFLOWS),
        "MACHINE_TRUST_ACTIVITIES": list(registry.MACHINE_TRUST_ACTIVITIES),
        "TWINS_WORKFLOWS": list(registry.TWINS_WORKFLOWS),
        "TWINS_ACTIVITIES": list(registry.TWINS_ACTIVITIES),
        "CONTRACTS_WORKFLOWS": list(registry.CONTRACTS_WORKFLOWS),
        "CONTRACTS_ACTIVITIES": list(registry.CONTRACTS_ACTIVITIES),
        "COMPLIANCE_WORKFLOWS": list(registry.COMPLIANCE_WORKFLOWS),
        "COMPLIANCE_ACTIVITIES": list(registry.COMPLIANCE_ACTIVITIES),
        "MAINTENANCE_WORKFLOWS": list(registry.MAINTENANCE_WORKFLOWS),
        "MAINTENANCE_ACTIVITIES": list(registry.MAINTENANCE_ACTIVITIES),
    }
    monkeypatch.setattr(registry, "discover_definitions", lambda: ())

    for items in (
        registry.ONBOARDING_WORKFLOWS,
        registry.ONBOARDING_ACTIVITIES,
        registry.MACHINE_TRUST_WORKFLOWS,
        registry.MACHINE_TRUST_ACTIVITIES,
        registry.TWINS_WORKFLOWS,
        registry.TWINS_ACTIVITIES,
        registry.CONTRACTS_WORKFLOWS,
        registry.CONTRACTS_ACTIVITIES,
        registry.COMPLIANCE_WORKFLOWS,
        registry.COMPLIANCE_ACTIVITIES,
        registry.MAINTENANCE_WORKFLOWS,
        registry.MAINTENANCE_ACTIVITIES,
    ):
        items.clear()

    try:
        with pytest.raises(RuntimeError, match="zero procedure definitions"):
            registry._populate_from_procedures()
    finally:
        for name, snapshot in snapshots.items():
            target = getattr(registry, name)
            target.clear()
            target.extend(snapshot)


def test_registry_mismatch_raises_when_requested(monkeypatch) -> None:
    monkeypatch.setattr(
        registry,
        "load_procedure_manifests",
        lambda: {
            "company-onboarding": procedure_catalog.ProcedureManifestInfo(
                module_name="company_onboarding",
                workflow_type="NotTheRegisteredWorkflow",
                task_queue="onboarding",
                search_attribute_keys=("tenant_id",),
            )
        },
    )

    with pytest.raises(RuntimeError, match="does not match procedure manifests"):
        registry.verify_registry(fail_on_mismatch=True)


def test_worker_bootstrap_modules_do_not_mutate_sys_path() -> None:
    assert "sys.path" not in inspect.getsource(procedure_catalog)
    assert "sys.path" not in inspect.getsource(registry)
