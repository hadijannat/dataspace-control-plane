"""Tests that registry lists exist and are the correct type."""
from src.bootstrap.procedure_catalog import load_procedure_manifests
from src.bootstrap.registry import (
    ONBOARDING_WORKFLOWS, ONBOARDING_ACTIVITIES,
    MACHINE_TRUST_WORKFLOWS, MACHINE_TRUST_ACTIVITIES,
    TWINS_WORKFLOWS, TWINS_ACTIVITIES,
    CONTRACTS_WORKFLOWS, CONTRACTS_ACTIVITIES,
    COMPLIANCE_WORKFLOWS, COMPLIANCE_ACTIVITIES,
    MAINTENANCE_WORKFLOWS, MAINTENANCE_ACTIVITIES,
    verify_registry,
)


def test_all_registry_lists_exist():
    assert isinstance(ONBOARDING_WORKFLOWS, list)
    assert isinstance(ONBOARDING_ACTIVITIES, list)
    assert isinstance(MACHINE_TRUST_WORKFLOWS, list)
    assert isinstance(TWINS_WORKFLOWS, list)
    assert isinstance(CONTRACTS_WORKFLOWS, list)
    assert isinstance(COMPLIANCE_WORKFLOWS, list)
    assert isinstance(MAINTENANCE_WORKFLOWS, list)


def test_verify_registry_does_not_raise():
    """verify_registry should log warnings but never raise."""
    verify_registry(warn_empty=False)


def test_registered_workflows_match_canonical_manifests():
    manifests = load_procedure_manifests()
    expected_workflow_types = {manifest.workflow_type for manifest in manifests.values()}
    actual_workflow_types = {
        workflow.__name__
        for workflows in (
            ONBOARDING_WORKFLOWS,
            MACHINE_TRUST_WORKFLOWS,
            TWINS_WORKFLOWS,
            CONTRACTS_WORKFLOWS,
            COMPLIANCE_WORKFLOWS,
            MAINTENANCE_WORKFLOWS,
        )
        for workflow in workflows
    }

    assert expected_workflow_types == actual_workflow_types
