"""
Worker host entry point.
Starts all worker groups concurrently. Each group polls its dedicated task queue.
"""
import asyncio
import structlog
import logging

from dataspace_control_plane_temporal_workers.settings import settings
from dataspace_control_plane_temporal_workers.bootstrap.client import create_temporal_client
from dataspace_control_plane_temporal_workers.bootstrap.search_attributes import (
    ensure_search_attributes,
)
from dataspace_control_plane_temporal_workers.bootstrap.registry import verify_registry
from dataspace_control_plane_temporal_workers.health import ProbeState, start_probe_server
from dataspace_control_plane_temporal_workers.telemetry import setup_telemetry
from dataspace_control_plane_temporal_workers.worker_groups.onboarding import (
    run_onboarding_worker,
)
from dataspace_control_plane_temporal_workers.worker_groups.trust import run_trust_worker
from dataspace_control_plane_temporal_workers.worker_groups.twins import run_twins_worker
from dataspace_control_plane_temporal_workers.worker_groups.contracts import (
    run_contracts_worker,
)
from dataspace_control_plane_temporal_workers.worker_groups.compliance import (
    run_compliance_worker,
)
from dataspace_control_plane_temporal_workers.worker_groups.maintenance import (
    run_maintenance_worker,
)

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    )
)
logger = structlog.get_logger(__name__)


async def main() -> None:
    setup_telemetry()
    probe_state = ProbeState()
    probe_server = await start_probe_server(probe_state, settings.health_port)

    try:
        client = await create_temporal_client()
        probe_state.temporal_connected = True
        await ensure_search_attributes(client)
        verify_registry(fail_on_mismatch=True)
        probe_state.registry_verified = True

        logger.info("workers.starting_all_groups", health_port=settings.health_port)
        tasks = [
            asyncio.create_task(run_onboarding_worker(client)),
            asyncio.create_task(run_trust_worker(client)),
            asyncio.create_task(run_twins_worker(client)),
            asyncio.create_task(run_contracts_worker(client)),
            asyncio.create_task(run_compliance_worker(client)),
            asyncio.create_task(run_maintenance_worker(client)),
        ]
        probe_state.workers_started = True
        await asyncio.gather(*tasks)
    except Exception as exc:
        probe_state.last_error = str(exc)
        raise
    finally:
        probe_server.close()
        await probe_server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
