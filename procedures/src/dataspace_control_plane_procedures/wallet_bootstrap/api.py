"""Public API surface for the wallet_bootstrap procedure.

apps/temporal-workers imports ALL_WORKFLOWS and ALL_ACTIVITIES (or calls
register()) to wire this procedure into its Worker instances.
"""
from __future__ import annotations

from dataspace_control_plane_procedures.wallet_bootstrap.workflow import WalletBootstrapWorkflow
from dataspace_control_plane_procedures.wallet_bootstrap.activities import ALL_ACTIVITIES
from dataspace_control_plane_procedures.wallet_bootstrap.manifest import MANIFEST, TASK_QUEUE
from dataspace_control_plane_procedures._shared.manifests import ProcedureManifest

ALL_WORKFLOWS = [WalletBootstrapWorkflow]
ALL_ACTIVITIES = ALL_ACTIVITIES  # re-export


def register(workflow_registry: dict | None = None, activity_registry: dict | None = None) -> None:
    """Side-effect registration into the global procedure registry.

    Call this from populate_from_procedures() in registry.py.
    """
    from dataspace_control_plane_procedures.registry import _register

    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


# Re-export manifest for convenience
__all__ = [
    "WalletBootstrapWorkflow",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "MANIFEST",
    "register",
]
