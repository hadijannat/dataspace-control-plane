from __future__ import annotations

import asyncio
import json

from app.application.dto.procedures import ProcedureStatusDTO
from app.services.procedure_status import load_procedure_status
from app.settings import settings

_TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED", "TERMINATED", "TIMED_OUT"}


def _status_key(snapshot: ProcedureStatusDTO) -> str:
    return json.dumps(snapshot.model_dump(mode="json"), sort_keys=True)


async def iter_workflow_status_events(
    workflow_id: str,
    *,
    gateway,
    pool,
    should_stop,
):
    last_key: str | None = None

    while True:
        if await should_stop():
            return
        snapshot = await load_procedure_status(
            workflow_id,
            gateway=gateway,
            pool=pool,
        )
        if snapshot is None:
            return

        current_key = _status_key(snapshot)
        if current_key != last_key:
            yield json.dumps(snapshot.model_dump(mode="json"))
            last_key = current_key
            if snapshot.status in _TERMINAL_STATES:
                return

        await asyncio.sleep(settings.stream_poll_interval_seconds)
