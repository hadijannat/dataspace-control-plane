"""Public API surface for the temporal_client infrastructure adapter.

Import only from this module when wiring the adapter in apps/ container code.
Internal implementation modules are considered private.

Example:
    from dataspace_control_plane_adapters.infrastructure.temporal_client.api import (
        create_temporal_client,
        WorkflowHandleHelper,
        TemporalWorkflowGateway,
        TemporalClientSettings,
    )
    cfg = TemporalClientSettings()
    client = await create_temporal_client(cfg)
    gateway = TemporalWorkflowGateway(client)
"""
from __future__ import annotations

from .client_factory import create_temporal_client
from .config import TemporalClientSettings
from .errors import (
    TemporalAdapterError,
    TemporalConnectionError,
    TemporalRpcError,
    WorkflowAlreadyStartedError,
    WorkflowNotFoundError,
    ScheduleNotFoundError,
)
from .health import TemporalHealthProbe
from .ports_impl import TemporalWorkflowGateway
from .queries import QueryExecutor
from .schedules import ScheduleManager
from .signals import SignalSender
from .updates import UpdateExecutor
from .workflow_handles import WorkflowHandleHelper

__all__ = [
    # Configuration
    "TemporalClientSettings",
    # Errors
    "TemporalAdapterError",
    "TemporalConnectionError",
    "TemporalRpcError",
    "WorkflowNotFoundError",
    "WorkflowAlreadyStartedError",
    "ScheduleNotFoundError",
    "TemporalHealthProbe",
    # Helpers
    "WorkflowHandleHelper",
    "SignalSender",
    "QueryExecutor",
    "UpdateExecutor",
    "ScheduleManager",
    # Port implementation
    "TemporalWorkflowGateway",
    # Factory
    "create_temporal_client",
]
