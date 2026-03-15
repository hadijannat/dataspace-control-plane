"""Procedure registry — maps procedure type strings to workflow/activity lists.

apps/temporal-workers imports this at startup to discover what to register.
procedures-lead populates WORKFLOW_REGISTRY and ACTIVITY_REGISTRY;
temporal-workers calls register_all() on its Worker instances.
"""
from __future__ import annotations
from typing import Any


# Maps task queue name → list of workflow classes registered on that queue.
# Populated by importing each procedure's api module.
WORKFLOW_REGISTRY: dict[str, list[Any]] = {
    "onboarding": [],
    "machine-trust": [],
    "twins-publication": [],
    "contracts-negotiation": [],
    "compliance": [],
    "maintenance": [],
}

# Maps task queue name → list of activity functions/classes registered on that queue.
ACTIVITY_REGISTRY: dict[str, list[Any]] = {
    "onboarding": [],
    "machine-trust": [],
    "twins-publication": [],
    "contracts-negotiation": [],
    "compliance": [],
    "maintenance": [],
}


def _register(queue: str, workflow: Any | None = None, activity: Any | None = None) -> None:
    if workflow is not None:
        WORKFLOW_REGISTRY.setdefault(queue, []).append(workflow)
    if activity is not None:
        ACTIVITY_REGISTRY.setdefault(queue, []).append(activity)


def populate_from_procedures() -> None:
    """Import each procedure's api module to trigger side-effect registration.

    Called once at worker startup before building Worker instances.
    Each api.register() appends workflow/activity objects to WORKFLOW_REGISTRY
    and ACTIVITY_REGISTRY via _register().
    """
    from dataspace_control_plane_procedures.company_onboarding.api import register as _r0
    _r0()
    from dataspace_control_plane_procedures.connector_bootstrap.api import register as _r1
    _r1()
    from dataspace_control_plane_procedures.delegate_tenant.api import register as _r2
    _r2()
    from dataspace_control_plane_procedures.dpp_provision.api import register as _r3
    _r3()
    from dataspace_control_plane_procedures.evidence_export.api import register as _r4
    _r4()
    from dataspace_control_plane_procedures.negotiate_contract.api import register as _r5
    _r5()
    from dataspace_control_plane_procedures.publish_asset.api import register as _r6
    _r6()
    from dataspace_control_plane_procedures.register_digital_twin.api import register as _r7
    _r7()
    from dataspace_control_plane_procedures.revoke_credentials.api import register as _r8
    _r8()
    from dataspace_control_plane_procedures.rotate_credentials.api import register as _r9
    _r9()
    from dataspace_control_plane_procedures.wallet_bootstrap.api import register as _r10
    _r10()


def verify_registry() -> None:
    """Log a warning for any queue with no registered workflows. Never raises."""
    import warnings
    for queue, workflows in WORKFLOW_REGISTRY.items():
        if not workflows:
            warnings.warn(
                f"Task queue '{queue}' has no registered workflows. "
                "Wire procedure packages in populate_from_procedures().",
                stacklevel=2,
            )
