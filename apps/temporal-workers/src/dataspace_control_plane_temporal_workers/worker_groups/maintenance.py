"""Maintenance worker group: credential rotation checks, stale negotiation sweeps."""
import asyncio
import structlog
from temporalio.client import Client
from temporalio.worker import Worker

from dataspace_control_plane_temporal_workers.bootstrap.task_queues import MAINTENANCE
from dataspace_control_plane_temporal_workers.bootstrap.registry import (
    MAINTENANCE_WORKFLOWS,
    MAINTENANCE_ACTIVITIES,
)
from dataspace_control_plane_temporal_workers.settings import settings

logger = structlog.get_logger(__name__)


async def run_maintenance_worker(client: Client) -> None:
    logger.info("worker_group.starting", queue=MAINTENANCE)
    async with Worker(
        client,
        task_queue=MAINTENANCE,
        workflows=MAINTENANCE_WORKFLOWS,
        activities=MAINTENANCE_ACTIVITIES,
        max_concurrent_activities=settings.max_concurrent_activities,
        max_concurrent_workflow_tasks=settings.max_concurrent_workflow_tasks,
    ):
        logger.info("worker_group.running", queue=MAINTENANCE)
        await asyncio.Future()
