"""
Onboarding worker group.
Polls: onboarding task queue.
Registers: company onboarding, connector bootstrap, wallet bootstrap procedures.
"""
import asyncio
import structlog
from temporalio.client import Client
from temporalio.worker import Worker

from src.bootstrap.task_queues import ONBOARDING
from src.bootstrap.registry import ONBOARDING_WORKFLOWS, ONBOARDING_ACTIVITIES
from src.settings import settings

logger = structlog.get_logger(__name__)


async def run_onboarding_worker(client: Client) -> None:
    logger.info("worker_group.starting", queue=ONBOARDING)
    async with Worker(
        client,
        task_queue=ONBOARDING,
        workflows=ONBOARDING_WORKFLOWS,
        activities=ONBOARDING_ACTIVITIES,
        max_concurrent_activities=settings.max_concurrent_activities,
        max_concurrent_workflow_tasks=settings.max_concurrent_workflow_tasks,
    ):
        logger.info("worker_group.running", queue=ONBOARDING)
        await asyncio.Future()  # run forever
