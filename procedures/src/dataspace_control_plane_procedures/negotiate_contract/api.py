"""Public API surface for the negotiate_contract procedure.

apps/temporal-workers imports ALL_WORKFLOWS and ALL_ACTIVITIES to build
its Temporal Worker instances. register() wires entries into the shared registry.
"""
from __future__ import annotations

from .manifest import MANIFEST, TASK_QUEUE
from .workflow import NegotiateContractWorkflow
from .activities import (
    check_credentials_and_offer,
    start_dsp_negotiation,
    submit_counteroffer,
    conclude_agreement,
    create_entitlement,
    issue_transfer_authorization,
    record_negotiation_evidence,
    cancel_negotiation,
)

ALL_WORKFLOWS = [NegotiateContractWorkflow]

ALL_ACTIVITIES = [
    check_credentials_and_offer,
    start_dsp_negotiation,
    submit_counteroffer,
    conclude_agreement,
    create_entitlement,
    issue_transfer_authorization,
    record_negotiation_evidence,
    cancel_negotiation,
]


def register() -> None:
    """Wire this procedure into the shared registry."""
    from dataspace_control_plane_procedures.registry import _register

    for wf in ALL_WORKFLOWS:
        _register(TASK_QUEUE, workflow=wf)
    for act in ALL_ACTIVITIES:
        _register(TASK_QUEUE, activity=act)


__all__ = ["NegotiateContractWorkflow", "MANIFEST", "ALL_WORKFLOWS", "ALL_ACTIVITIES", "register"]
