"""
Command objects for procedure operations (write side of CQRS-lite).

Commands are immutable value objects that carry all the information needed to
start or cancel a durable procedure. They are constructed by route handlers
and handed to service/gateway facades; no business logic lives here.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StartProcedureCommand:
    """
    Intent to launch a new durable procedure via Temporal.

    Attributes
    ----------
    procedure_type:
        Logical procedure name used to route to the correct task queue and
        workflow type, e.g. ``"company-onboarding"`` or ``"contract-negotiation"``.
    tenant_id:
        Tenant scope under which the procedure executes.
    legal_entity_id:
        Optional legal-entity identifier when the procedure is bound to a
        specific legal entity within the tenant.
    payload:
        Free-form dict forwarded verbatim as workflow input arguments.
    idempotency_key:
        Optional caller-supplied key used to deduplicate concurrent or
        retried requests. When present it becomes the Temporal workflow_id.
    actor_subject:
        The ``sub`` claim of the authenticated JWT — recorded in audit events.
    """

    procedure_type: str
    tenant_id: str
    legal_entity_id: str | None
    payload: dict[str, Any]
    idempotency_key: str | None
    actor_subject: str


@dataclass(frozen=True)
class CancelProcedureCommand:
    """
    Intent to cancel a running durable procedure.

    Attributes
    ----------
    workflow_id:
        Temporal workflow identifier of the procedure to cancel.
    tenant_id:
        Tenant scope — used for authorisation checks before signalling.
    reason:
        Human-readable cancellation reason recorded in the audit event.
    actor_subject:
        The ``sub`` claim of the authenticated JWT — recorded in audit events.
    """

    workflow_id: str
    tenant_id: str
    reason: str
    actor_subject: str
