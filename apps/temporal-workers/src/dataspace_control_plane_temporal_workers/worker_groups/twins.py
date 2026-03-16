"""Twins-publication worker group: register-digital-twin, publish-asset procedures."""
import asyncio
import structlog
from temporalio.client import Client
from temporalio.worker import Worker

from dataspace_control_plane_temporal_workers.bootstrap.task_queues import (
    TWINS_PUBLICATION,
)
from dataspace_control_plane_temporal_workers.bootstrap.registry import (
    TWINS_WORKFLOWS,
    TWINS_ACTIVITIES,
)
from dataspace_control_plane_temporal_workers.settings import settings

logger = structlog.get_logger(__name__)


async def run_twins_worker(client: Client) -> None:
    logger.info("worker_group.starting", queue=TWINS_PUBLICATION)
    async with Worker(
        client,
        task_queue=TWINS_PUBLICATION,
        workflows=TWINS_WORKFLOWS,
        activities=TWINS_ACTIVITIES,
        max_concurrent_activities=settings.max_concurrent_activities,
        max_concurrent_workflow_tasks=settings.max_concurrent_workflow_tasks,
    ):
        logger.info("worker_group.running", queue=TWINS_PUBLICATION)
        await asyncio.Future()
