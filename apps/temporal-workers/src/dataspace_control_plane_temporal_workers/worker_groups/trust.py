"""Machine-trust worker group: wallet bootstrap, credential rotation, DID/key management."""
import asyncio
import structlog
from temporalio.client import Client
from temporalio.worker import Worker

from dataspace_control_plane_temporal_workers.bootstrap.task_queues import MACHINE_TRUST
from dataspace_control_plane_temporal_workers.bootstrap.registry import (
    MACHINE_TRUST_WORKFLOWS,
    MACHINE_TRUST_ACTIVITIES,
)
from dataspace_control_plane_temporal_workers.settings import settings

logger = structlog.get_logger(__name__)


async def run_trust_worker(client: Client) -> None:
    logger.info("worker_group.starting", queue=MACHINE_TRUST)
    async with Worker(
        client,
        task_queue=MACHINE_TRUST,
        workflows=MACHINE_TRUST_WORKFLOWS,
        activities=MACHINE_TRUST_ACTIVITIES,
        max_concurrent_activities=settings.max_concurrent_activities,
        max_concurrent_workflow_tasks=settings.max_concurrent_workflow_tasks,
    ):
        logger.info("worker_group.running", queue=MACHINE_TRUST)
        await asyncio.Future()
