"""
Temporal testing environment fixtures.
Uses temporalio.testing.WorkflowEnvironment for time-skipping unit-level workflow tests.
Requires the temporalio package.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Workflow environment
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
@pytest.mark.anyio
async def temporal_env():
    """
    Session-scoped time-skipping Temporal WorkflowEnvironment.

    Requires temporalio. Yields env, shuts down on teardown.
    """
    pytest.importorskip("temporalio", reason="temporalio required for temporal_env")
    from temporalio.testing import WorkflowEnvironment

    env = await WorkflowEnvironment.start_time_skipping()
    yield env
    await env.shutdown()


# ---------------------------------------------------------------------------
# Temporal client
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def temporal_client(temporal_env):
    """Session-scoped Temporal client from the time-skipping environment."""
    return temporal_env.client


# ---------------------------------------------------------------------------
# Temporal worker
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
@pytest.mark.anyio
async def temporal_worker(temporal_client, request: pytest.FixtureRequest):
    """
    Function-scoped Temporal Worker.

    task_queue is read from request.param, defaulting to 'test-queue'.
    Yields the worker. Cancels on teardown.
    """
    pytest.importorskip("temporalio", reason="temporalio required for temporal_worker")
    from temporalio.worker import Worker

    task_queue = getattr(request, "param", "test-queue")
    worker = Worker(
        client=temporal_client,
        task_queue=task_queue,
        workflows=[],
        activities=[],
    )
    async with worker:
        yield worker
