"""Public API surface for the negotiate_contract procedure.

apps/temporal-workers imports ALL_WORKFLOWS and ALL_ACTIVITIES to build
its Temporal Worker instances. register() wires entries into the shared registry.
"""
from __future__ import annotations

from dataspace_control_plane_procedures.registry import build_definition

from .manifest import MANIFEST, TASK_QUEUE, WORKFLOW_TYPE
from .input import NegotiationCarryState, NegotiationResult, NegotiationStartInput, NegotiationStatusQuery
from .workflow import NegotiateContractWorkflow
from .messages import AcceptCounteroffer, CounterOfferResult, RejectNegotiation, RejectionResult
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

WorkflowClass = NegotiateContractWorkflow
StartInput = NegotiationStartInput
Result = NegotiationResult
StatusQuery = NegotiationStatusQuery
manifest = MANIFEST
definition = build_definition(
    api_module_name=__name__,
    manifest=MANIFEST,
    start_input_type=NegotiationStartInput,
    status_query_type=NegotiationStatusQuery,
    workflow_types=ALL_WORKFLOWS,
    activity_functions=ALL_ACTIVITIES,
)


def register() -> None:
    """Wire this procedure into the shared registry."""
    from dataspace_control_plane_procedures.registry import _register_definition

    _register_definition(definition)


__all__ = [
    "NegotiateContractWorkflow",
    "MANIFEST",
    "WORKFLOW_TYPE",
    "TASK_QUEUE",
    "NegotiationStartInput",
    "NegotiationResult",
    "NegotiationStatusQuery",
    "NegotiationCarryState",
    "AcceptCounteroffer",
    "CounterOfferResult",
    "RejectNegotiation",
    "RejectionResult",
    "WorkflowClass",
    "StartInput",
    "Result",
    "StatusQuery",
    "manifest",
    "definition",
    "ALL_WORKFLOWS",
    "ALL_ACTIVITIES",
    "register",
]
