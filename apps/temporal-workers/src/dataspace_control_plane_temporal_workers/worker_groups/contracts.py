"""Contracts-negotiation worker group: negotiate-contract, dpp-provision procedures."""
import asyncio
import structlog
from temporalio.client import Client
from temporalio.worker import Worker

from dataspace_control_plane_temporal_workers.bootstrap.task_queues import (
    CONTRACTS_NEGOTIATION,
)
from dataspace_control_plane_temporal_workers.bootstrap.registry import (
    CONTRACTS_WORKFLOWS,
    CONTRACTS_ACTIVITIES,
)
from dataspace_control_plane_temporal_workers.settings import settings

logger = structlog.get_logger(__name__)


async def run_contracts_worker(client: Client) -> None:
    logger.info("worker_group.starting", queue=CONTRACTS_NEGOTIATION)
    async with Worker(
        client,
        task_queue=CONTRACTS_NEGOTIATION,
        workflows=CONTRACTS_WORKFLOWS,
        activities=CONTRACTS_ACTIVITIES,
        max_concurrent_activities=settings.max_concurrent_activities,
        max_concurrent_workflow_tasks=settings.max_concurrent_workflow_tasks,
    ):
        logger.info("worker_group.running", queue=CONTRACTS_NEGOTIATION)
        await asyncio.Future()
