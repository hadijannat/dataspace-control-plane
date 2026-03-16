"""Compliance worker group: evidence-export, compliance gap scans."""
import asyncio
import structlog
from temporalio.client import Client
from temporalio.worker import Worker

from dataspace_control_plane_temporal_workers.bootstrap.task_queues import COMPLIANCE
from dataspace_control_plane_temporal_workers.bootstrap.registry import (
    COMPLIANCE_WORKFLOWS,
    COMPLIANCE_ACTIVITIES,
)
from dataspace_control_plane_temporal_workers.settings import settings

logger = structlog.get_logger(__name__)


async def run_compliance_worker(client: Client) -> None:
    logger.info("worker_group.starting", queue=COMPLIANCE)
    async with Worker(
        client,
        task_queue=COMPLIANCE,
        workflows=COMPLIANCE_WORKFLOWS,
        activities=COMPLIANCE_ACTIVITIES,
        max_concurrent_activities=settings.max_concurrent_activities,
        max_concurrent_workflow_tasks=settings.max_concurrent_workflow_tasks,
    ):
        logger.info("worker_group.running", queue=COMPLIANCE)
        await asyncio.Future()
