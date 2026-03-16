"""
Test fixtures for Temporal worker registration and replay tests.
Use with pytest and temporalio.testing.WorkflowEnvironment.
"""
from __future__ import annotations
import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from dataspace_control_plane_temporal_workers.bootstrap.task_queues import (
    ONBOARDING, MACHINE_TRUST, TWINS_PUBLICATION,
    CONTRACTS_NEGOTIATION, COMPLIANCE, MAINTENANCE,
)
from dataspace_control_plane_temporal_workers.bootstrap.registry import (
    ONBOARDING_WORKFLOWS, ONBOARDING_ACTIVITIES,
    MACHINE_TRUST_WORKFLOWS, MACHINE_TRUST_ACTIVITIES,
    TWINS_WORKFLOWS, TWINS_ACTIVITIES,
    CONTRACTS_WORKFLOWS, CONTRACTS_ACTIVITIES,
    COMPLIANCE_WORKFLOWS, COMPLIANCE_ACTIVITIES,
    MAINTENANCE_WORKFLOWS, MAINTENANCE_ACTIVITIES,
)


@pytest.fixture(scope="session")
async def temporal_env():
    """Session-scoped in-process Temporal environment for integration tests."""
    async with await WorkflowEnvironment.start_local() as env:
        yield env


def make_worker(env: WorkflowEnvironment, task_queue: str) -> Worker:
    """
    Create a worker for the given task queue using the live registry.
    Useful for replay and registration tests.
    """
    registry = {
        ONBOARDING: (ONBOARDING_WORKFLOWS, ONBOARDING_ACTIVITIES),
        MACHINE_TRUST: (MACHINE_TRUST_WORKFLOWS, MACHINE_TRUST_ACTIVITIES),
        TWINS_PUBLICATION: (TWINS_WORKFLOWS, TWINS_ACTIVITIES),
        CONTRACTS_NEGOTIATION: (CONTRACTS_WORKFLOWS, CONTRACTS_ACTIVITIES),
        COMPLIANCE: (COMPLIANCE_WORKFLOWS, COMPLIANCE_ACTIVITIES),
        MAINTENANCE: (MAINTENANCE_WORKFLOWS, MAINTENANCE_ACTIVITIES),
    }
    workflows, activities = registry[task_queue]
    return Worker(
        env.client,
        task_queue=task_queue,
        workflows=workflows,
        activities=activities,
    )
