"""
Worker host entry point.
Starts all worker groups concurrently. Each group polls its dedicated task queue.
"""
import asyncio
import structlog
import logging

from src.settings import settings
from src.bootstrap.client import create_temporal_client
from src.bootstrap.search_attributes import ensure_search_attributes
from src.bootstrap.registry import verify_registry
from src.telemetry import setup_telemetry
from src.worker_groups.onboarding import run_onboarding_worker
from src.worker_groups.trust import run_trust_worker
from src.worker_groups.twins import run_twins_worker
from src.worker_groups.contracts import run_contracts_worker
from src.worker_groups.compliance import run_compliance_worker
from src.worker_groups.maintenance import run_maintenance_worker

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    )
)
logger = structlog.get_logger(__name__)


async def main() -> None:
    setup_telemetry()

    client = await create_temporal_client()
    await ensure_search_attributes(client)
    verify_registry(fail_on_mismatch=True)

    logger.info("workers.starting_all_groups")

    await asyncio.gather(
        run_onboarding_worker(client),
        run_trust_worker(client),
        run_twins_worker(client),
        run_contracts_worker(client),
        run_compliance_worker(client),
        run_maintenance_worker(client),
    )


if __name__ == "__main__":
    asyncio.run(main())
