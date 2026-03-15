from __future__ import annotations

import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from temporalio.api.operatorservice.v1 import AddSearchAttributesRequest
from temporalio.testing import WorkflowEnvironment
from temporalio.service import RPCError


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


from dataspace_control_plane_procedures._shared.search_attributes import ALL_SA_KEYS


def unique_task_queue(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


async def _ensure_search_attributes(env: WorkflowEnvironment) -> None:
    for key in ALL_SA_KEYS:
        try:
            await env.client.operator_service.add_search_attributes(
                AddSearchAttributesRequest(
                    namespace=env.client.namespace,
                    search_attributes={key.name: int(key.indexed_value_type)},
                )
            )
        except RPCError as exc:
            if "already exists" not in str(exc).lower():
                raise


@pytest.fixture
def time_skipping_env():
    @asynccontextmanager
    async def _time_skipping_env():
        env = await WorkflowEnvironment.start_time_skipping()
        await _ensure_search_attributes(env)
        try:
            yield env
        finally:
            await env.shutdown()

    return _time_skipping_env
