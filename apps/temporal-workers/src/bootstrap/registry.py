"""
Workflow and activity registry for all temporal worker groups.

Delegates to the canonical procedures/ package registry at module load time.
Worker groups import the module-level list objects here and see the fully
populated registries when this module is first imported.

If the procedures package is not installed, workers start with empty registries
and log a warning — the Temporal namespace will start but cannot execute tasks.
"""
from __future__ import annotations

from typing import Any

import structlog
from src.bootstrap.procedure_catalog import import_procedures_package, load_procedure_manifests

logger = structlog.get_logger(__name__)

# ── Per-queue workflow and activity lists ─────────────────────────────────────
# Worker groups import these directly; extend() in _populate() preserves
# list identity so all importers see the same populated object.

ONBOARDING_WORKFLOWS: list[Any] = []
ONBOARDING_ACTIVITIES: list[Any] = []

MACHINE_TRUST_WORKFLOWS: list[Any] = []
MACHINE_TRUST_ACTIVITIES: list[Any] = []

TWINS_WORKFLOWS: list[Any] = []
TWINS_ACTIVITIES: list[Any] = []

CONTRACTS_WORKFLOWS: list[Any] = []
CONTRACTS_ACTIVITIES: list[Any] = []

COMPLIANCE_WORKFLOWS: list[Any] = []
COMPLIANCE_ACTIVITIES: list[Any] = []

MAINTENANCE_WORKFLOWS: list[Any] = []
MAINTENANCE_ACTIVITIES: list[Any] = []


def _populate_from_procedures() -> bool:
    """Delegate to procedures.registry.populate_from_procedures().

    Extends each queue's list with the workflow/activity objects declared in
    the procedures package. Called once at module load — subsequent imports
    of this module see the already-populated lists.

    Returns True if procedures package was available, False otherwise.
    """
    try:
        procedures_pkg = import_procedures_package()
        from dataspace_control_plane_procedures.registry import (
            ACTIVITY_REGISTRY,
            WORKFLOW_REGISTRY,
            populate_from_procedures,
        )
    except ImportError:
        logger.warning(
            "registry.procedures_not_installed",
            message=(
                "dataspace-control-plane-procedures not installed — "
                "workers will start with empty task queues. "
                "Add it to pyproject.toml dependencies."
            ),
        )
        return False

    populate_from_procedures()

    # Extend (not assign) to preserve the list identity already imported by
    # worker group modules that reference ONBOARDING_WORKFLOWS etc. directly.
    ONBOARDING_WORKFLOWS.extend(WORKFLOW_REGISTRY.get("onboarding", []))
    ONBOARDING_ACTIVITIES.extend(ACTIVITY_REGISTRY.get("onboarding", []))

    MACHINE_TRUST_WORKFLOWS.extend(WORKFLOW_REGISTRY.get("machine-trust", []))
    MACHINE_TRUST_ACTIVITIES.extend(ACTIVITY_REGISTRY.get("machine-trust", []))

    TWINS_WORKFLOWS.extend(WORKFLOW_REGISTRY.get("twins-publication", []))
    TWINS_ACTIVITIES.extend(ACTIVITY_REGISTRY.get("twins-publication", []))

    CONTRACTS_WORKFLOWS.extend(WORKFLOW_REGISTRY.get("contracts-negotiation", []))
    CONTRACTS_ACTIVITIES.extend(ACTIVITY_REGISTRY.get("contracts-negotiation", []))

    COMPLIANCE_WORKFLOWS.extend(WORKFLOW_REGISTRY.get("compliance", []))
    COMPLIANCE_ACTIVITIES.extend(ACTIVITY_REGISTRY.get("compliance", []))

    MAINTENANCE_WORKFLOWS.extend(WORKFLOW_REGISTRY.get("maintenance", []))
    MAINTENANCE_ACTIVITIES.extend(ACTIVITY_REGISTRY.get("maintenance", []))

    total_workflows = sum(
        len(lst)
        for lst in [
            ONBOARDING_WORKFLOWS,
            MACHINE_TRUST_WORKFLOWS,
            TWINS_WORKFLOWS,
            CONTRACTS_WORKFLOWS,
            COMPLIANCE_WORKFLOWS,
            MAINTENANCE_WORKFLOWS,
        ]
    )
    total_activities = sum(
        len(lst)
        for lst in [
            ONBOARDING_ACTIVITIES,
            MACHINE_TRUST_ACTIVITIES,
            TWINS_ACTIVITIES,
            CONTRACTS_ACTIVITIES,
            COMPLIANCE_ACTIVITIES,
            MAINTENANCE_ACTIVITIES,
        ]
    )
    logger.info(
        "registry.populated",
        workflows=total_workflows,
        activities=total_activities,
    )
    return True


# Populate at module load — all subsequent imports see fully-registered lists.
_populate_from_procedures()


def _group_workflows() -> dict[str, list[Any]]:
    return {
        "onboarding": ONBOARDING_WORKFLOWS,
        "machine-trust": MACHINE_TRUST_WORKFLOWS,
        "twins-publication": TWINS_WORKFLOWS,
        "contracts-negotiation": CONTRACTS_WORKFLOWS,
        "compliance": COMPLIANCE_WORKFLOWS,
        "maintenance": MAINTENANCE_WORKFLOWS,
    }


def verify_registry(warn_empty: bool = True, fail_on_mismatch: bool = False) -> None:
    """Validate queue registrations against canonical procedure manifests."""
    groups = _group_workflows()
    expected_by_queue: dict[str, set[str]] = {}
    for manifest in load_procedure_manifests().values():
        expected_by_queue.setdefault(manifest.task_queue, set()).add(manifest.workflow_type)

    mismatches: list[str] = []
    for queue, workflows in groups.items():
        actual = {workflow.__name__ for workflow in workflows}
        expected = expected_by_queue.get(queue, set())
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        if warn_empty and not actual:
            logger.warning(
                "registry.empty_queue",
                queue=queue,
                message="No workflows registered — worker cannot process tasks for this queue",
            )
        if missing or unexpected:
            mismatches.append(
                f"{queue}: missing={missing or '-'} unexpected={unexpected or '-'}"
            )

    if mismatches and fail_on_mismatch:
        raise RuntimeError(
            "Temporal worker registry does not match procedure manifests: "
            + "; ".join(mismatches)
        )
    for mismatch in mismatches:
        logger.warning("registry.mismatch", detail=mismatch)
