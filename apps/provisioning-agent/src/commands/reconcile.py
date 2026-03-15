"""
Reconcile command: periodic convergence loop.
Runs plan → apply on a schedule. Safe to run as a Kubernetes Job or CronJob.
"""
import asyncio
import structlog
from src.commands.plan import run_plan
from src.commands.apply import run_apply
from src.state.locks import file_lock

logger = structlog.get_logger(__name__)


async def run_reconcile(interval_seconds: int = 300, dry_run: bool = False) -> None:
    logger.info("reconcile.start", interval_seconds=interval_seconds)
    while True:
        try:
            with file_lock("reconcile-cycle"):
                diff = await run_plan()
                await run_apply(diff, dry_run=dry_run)
        except Exception as exc:
            logger.error("reconcile.cycle_error", error=str(exc), exc_info=True)
        logger.info("reconcile.sleeping", seconds=interval_seconds)
        await asyncio.sleep(interval_seconds)
