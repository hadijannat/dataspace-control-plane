"""
Audit event emission.

Structured audit events are emitted via structlog to the ``audit`` logger.
Events carry a consistent schema so they can be forwarded to a persistent
audit log (Postgres, SIEM, or an append-only event store) by the log
shipping pipeline without schema changes.

A downstream task will wire ``emit`` to a direct asyncpg INSERT once the
``audit_events`` table is provisioned; until then structured logs provide
the durable record.
"""
from typing import Any

import structlog

audit_log = structlog.get_logger("audit")


async def emit(
    event_type: str,
    actor_subject: str,
    tenant_id: str | None,
    resource_type: str,
    resource_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Emit a structured audit event.

    All fields are logged at INFO level under the ``audit`` logger namespace.
    Downstream log shippers (Fluent Bit, Vector, etc.) can filter on the
    logger name to route audit records to a dedicated sink.

    Parameters
    ----------
    event_type:
        Dot-namespaced event identifier, e.g. ``"procedure.started"`` or
        ``"tenant.created"``.
    actor_subject:
        The ``sub`` claim of the authenticated JWT — uniquely identifies the
        human operator or service account that triggered the event.
    tenant_id:
        The tenant scope in which the event occurred, or ``None`` for
        platform-level events.
    resource_type:
        The kind of resource affected, e.g. ``"procedure"``, ``"tenant"``,
        ``"connector"``.
    resource_id:
        The unique identifier of the affected resource (e.g. workflow_id,
        tenant_id, connector_id).
    metadata:
        Optional free-form dict of additional context (request correlation
        IDs, procedure types, payload summaries, etc.). Merged into the
        log record at the top level — avoid nesting to keep queries simple.
    """
    audit_log.info(
        event_type,
        actor=actor_subject,
        tenant_id=tenant_id,
        resource_type=resource_type,
        resource_id=resource_id,
        **(metadata or {}),
    )
