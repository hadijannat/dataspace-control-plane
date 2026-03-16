"""
Workflow and activity registry for all temporal worker groups.

Delegates to the canonical procedures package definitions at module load time.
Worker groups import the module-level list objects here and see the fully
populated registries when this module is first imported.
"""
from __future__ import annotations

from typing import Any

import structlog
from dataspace_control_plane_procedures import discover_definitions
from dataspace_control_plane_temporal_workers.bootstrap.procedure_catalog import (
    load_procedure_manifests,
)

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
    """Populate queue-local registry lists from explicit procedure definitions."""
    definitions = discover_definitions()
    if not definitions:
        raise RuntimeError("Temporal worker startup aborted: zero procedure definitions discovered")

    by_queue: dict[str, tuple[list[Any], list[Any]]] = {}
    for definition in definitions:
        workflows: list[Any]
        activities: list[Any]
        workflows, activities = by_queue.setdefault(
            definition.task_queue,
            ([], []),
        )
        workflows.extend(definition.workflow_types)
        activities.extend(definition.activity_functions)

    # Extend (not assign) to preserve the list identity already imported by
    # worker group modules that reference ONBOARDING_WORKFLOWS etc. directly.
    onboarding_workflows, onboarding_activities = by_queue.get("onboarding", ([], []))
    ONBOARDING_WORKFLOWS.extend(onboarding_workflows)
    ONBOARDING_ACTIVITIES.extend(onboarding_activities)

    trust_workflows, trust_activities = by_queue.get("machine-trust", ([], []))
    MACHINE_TRUST_WORKFLOWS.extend(trust_workflows)
    MACHINE_TRUST_ACTIVITIES.extend(trust_activities)

    twins_workflows, twins_activities = by_queue.get("twins-publication", ([], []))
    TWINS_WORKFLOWS.extend(twins_workflows)
    TWINS_ACTIVITIES.extend(twins_activities)

    contracts_workflows, contracts_activities = by_queue.get(
        "contracts-negotiation", ([], [])
    )
    CONTRACTS_WORKFLOWS.extend(contracts_workflows)
    CONTRACTS_ACTIVITIES.extend(contracts_activities)

    compliance_workflows, compliance_activities = by_queue.get("compliance", ([], []))
    COMPLIANCE_WORKFLOWS.extend(compliance_workflows)
    COMPLIANCE_ACTIVITIES.extend(compliance_activities)

    maintenance_workflows, maintenance_activities = by_queue.get("maintenance", ([], []))
    MAINTENANCE_WORKFLOWS.extend(maintenance_workflows)
    MAINTENANCE_ACTIVITIES.extend(maintenance_activities)

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
