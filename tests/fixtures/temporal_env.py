"""Temporal testing environment fixtures."""
from __future__ import annotations

import asyncio

import pytest


@pytest.fixture(scope="session")
def temporal_env():
    """Session-scoped time-skipping Temporal WorkflowEnvironment."""
    pytest.importorskip("temporalio", reason="temporalio required for temporal_env")
    from temporalio.testing import WorkflowEnvironment

    loop = asyncio.new_event_loop()
    try:
        env = loop.run_until_complete(WorkflowEnvironment.start_time_skipping())
        setattr(env, "_fixture_loop", loop)
        yield env
        loop.run_until_complete(env.shutdown())
    finally:
        loop.close()


@pytest.fixture(scope="session")
def temporal_client(temporal_env):
    """Session-scoped Temporal client from the time-skipping environment."""
    return temporal_env.client


@pytest.fixture(scope="function")
def temporal_worker(temporal_client, request: pytest.FixtureRequest):
    """Function-scoped Temporal worker started on the shared test loop."""
    pytest.importorskip("temporalio", reason="temporalio required for temporal_worker")
    from temporalio.worker import Worker

    config = getattr(request, "param", {})
    if isinstance(config, str):
        config = {"task_queue": config}

    task_queue = config.get("task_queue", "test-queue")
    worker = Worker(
        client=temporal_client,
        task_queue=task_queue,
        workflows=config.get("workflows", []),
        activities=config.get("activities", []),
    )
    fixture_loop = getattr(request.getfixturevalue("temporal_env"), "_fixture_loop", None)
    active_loop = fixture_loop
    if active_loop is None:
        raise RuntimeError("Temporal test loop is not available")

    active_loop.run_until_complete(worker.__aenter__())
    try:
        yield worker
    finally:
        active_loop.run_until_complete(worker.__aexit__(None, None, None))
