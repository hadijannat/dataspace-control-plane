"""Temporal client adapter-specific error hierarchy.

Rules:
- TemporalAdapterError is the root of all Temporal-layer exceptions.
- All callers translate these into core-layer errors at the service boundary.
- Never include workflow payload contents, correlation IDs, or tenant data in
  error messages beyond what is needed to identify the failed workflow.
"""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.errors import (
    AdapterConflictError,
    AdapterError,
    AdapterNotFoundError,
)


class TemporalAdapterError(AdapterError):
    """Root for all Temporal client adapter errors."""


class WorkflowNotFoundError(AdapterNotFoundError):
    """Raised when the target workflow execution does not exist.

    Subclasses AdapterNotFoundError so callers can catch the shared base type.
    """

    def __init__(self, workflow_id: str, run_id: str | None = None) -> None:
        rid_part = f" run_id={run_id!r}" if run_id else ""
        super().__init__(
            f"Temporal workflow {workflow_id!r}{rid_part} not found.",
            upstream_code="workflow_not_found",
        )
        self.workflow_id = workflow_id
        self.run_id = run_id


class WorkflowAlreadyStartedError(AdapterConflictError):
    """Raised when a workflow with the same workflow_id is already running.

    Subclasses AdapterConflictError so callers can catch the shared base type.
    """

    def __init__(self, workflow_id: str) -> None:
        super().__init__(
            f"Temporal workflow {workflow_id!r} is already running.",
            upstream_code="workflow_already_started",
        )
        self.workflow_id = workflow_id


class TemporalConnectionError(TemporalAdapterError):
    """Raised when the gRPC connection to Temporal cannot be established."""


class TemporalRpcError(TemporalAdapterError):
    """Raised when a Temporal gRPC RPC returns a non-retryable error."""


class ScheduleNotFoundError(AdapterNotFoundError):
    """Raised when the target schedule does not exist in Temporal."""

    def __init__(self, schedule_id: str) -> None:
        super().__init__(
            f"Temporal schedule {schedule_id!r} not found.",
            upstream_code="schedule_not_found",
        )
        self.schedule_id = schedule_id
