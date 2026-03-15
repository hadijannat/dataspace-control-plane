from __future__ import annotations

import asyncio
import json

import structlog

from app.application.dto.procedures import ProcedureStatusDTO
from app.services.procedure_status import load_procedure_status
from app.settings import settings

logger = structlog.get_logger(__name__)

_TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED", "TERMINATED", "TIMED_OUT"}


def _status_key(snapshot: ProcedureStatusDTO) -> tuple:
    return (snapshot.status, snapshot.updated_at, snapshot.failure_message)


async def iter_workflow_status_events(
    workflow_id: str,
    *,
    gateway,
    pool,
    should_stop,
):
    """Poll ``load_procedure_status`` and yield SSE-ready JSON snapshots on change.

    Behaviour:
    - Polls ``load_procedure_status`` at ``settings.stream_poll_interval_seconds``
      intervals (default: 2.0 s).
    - Each time the status snapshot differs from the last seen snapshot, the new
      snapshot is yielded as a JSON string.
    - The generator terminates when the workflow reaches a terminal state or the
      client disconnects (``should_stop`` returns ``True``).
    - Terminal states: COMPLETED, FAILED, CANCELLED, TERMINATED, TIMED_OUT.
    """
    last_key: tuple | None = None

    while True:
        if await should_stop():
            return
        try:
            snapshot = await asyncio.wait_for(
                load_procedure_status(
                    workflow_id,
                    gateway=gateway,
                    pool=pool,
                ),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "workflow_streams.load_status_timeout",
                workflow_id=workflow_id,
            )
            await asyncio.sleep(settings.stream_poll_interval_seconds)
            continue

        if snapshot is None:
            return

        current_key = _status_key(snapshot)
        if current_key != last_key:
            yield json.dumps(snapshot.model_dump(mode="json"))
            last_key = current_key
            if snapshot.status in _TERMINAL_STATES:
                return

        await asyncio.sleep(settings.stream_poll_interval_seconds)
