"""Temporal schedule management.

Provides typed wrappers for creating, deleting, and listing Temporal schedules.
Schedules drive recurring workflow executions (cron or interval triggers).

Usage:
    mgr = ScheduleManager(client)
    await mgr.create_schedule(
        schedule_id="daily-sweep",
        workflow_type="StaleNegotiationSweep",
        cron="0 2 * * *",
        input={"tenant_id": "t-001"},
    )
"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from .errors import ScheduleNotFoundError, TemporalAdapterError, TemporalRpcError

if TYPE_CHECKING:
    import temporalio.client

logger = logging.getLogger(__name__)


class ScheduleManager:
    """Manages Temporal schedule lifecycle (create, delete, list).

    Schedules use the Temporal schedule API, not Cron Workflows.
    Each schedule has a unique *schedule_id* within the configured namespace.
    """

    def __init__(
        self,
        client: "temporalio.client.Client",
        *,
        default_task_queue: str = "dataspace-control-plane",
    ) -> None:
        self._client = client
        self._default_task_queue = default_task_queue

    async def create_schedule(
        self,
        schedule_id: str,
        workflow_type: str,
        cron: str,
        input: Any,
        *,
        task_queue: str | None = None,
        timezone: str = "UTC",
        paused: bool = False,
    ) -> None:
        """Create a new schedule that triggers *workflow_type* on a cron expression.

        Args:
            schedule_id:   Unique identifier for the schedule within the namespace.
            workflow_type: Temporal workflow type name.
            cron:          Standard cron expression (e.g. ``"0 2 * * *"``).
            input:         Serialisable workflow input passed on each trigger.
            task_queue:    Task queue for triggered workflows. Defaults to adapter default.
            timezone:      IANA timezone for the cron schedule (default: ``"UTC"``).
            paused:        Start the schedule in paused state (default: False).

        Raises:
            TemporalRpcError: Temporal returned an error creating the schedule.
        """
        # Heavy SDK import deferred to avoid mandatory dependency at module load time.
        import temporalio.client

        queue = task_queue or self._default_task_queue

        try:
            schedule = temporalio.client.Schedule(
                action=temporalio.client.ScheduleActionStartWorkflow(
                    workflow_type,
                    input,
                    id=f"{schedule_id}-{{schedule_action_id}}",
                    task_queue=queue,
                ),
                spec=temporalio.client.ScheduleSpec(
                    cron_expressions=[cron],
                    # TODO: production impl — add jitter and calendar-spec support
                ),
                state=temporalio.client.ScheduleState(paused=paused),
            )
            await self._client.create_schedule(
                schedule_id,
                schedule=schedule,
            )
            logger.info(
                "Created Temporal schedule id=%s workflow=%s cron=%s",
                schedule_id, workflow_type, cron,
            )
        except Exception as exc:
            raise TemporalRpcError(
                f"Failed to create schedule id={schedule_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    async def delete_schedule(self, schedule_id: str) -> None:
        """Delete a schedule by *schedule_id*.

        Deleting a schedule does not terminate any in-flight workflows it started.

        Args:
            schedule_id: Unique schedule identifier.

        Raises:
            ScheduleNotFoundError: The schedule does not exist.
            TemporalRpcError:      Any other Temporal RPC error.
        """
        try:
            handle = self._client.get_schedule_handle(schedule_id)
            await handle.delete()
            logger.info("Deleted Temporal schedule id=%s", schedule_id)
        except Exception as exc:
            exc_str = str(exc).lower()
            if "not found" in exc_str:
                raise ScheduleNotFoundError(schedule_id) from exc
            raise TemporalRpcError(
                f"Failed to delete schedule id={schedule_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    async def list_schedules(self) -> list[dict[str, Any]]:
        """Return a list of schedule summaries for the configured namespace.

        Returns:
            List of dicts with keys: schedule_id, workflow_type, cron, paused.

        Raises:
            TemporalRpcError: Any Temporal RPC error during listing.
        """
        try:
            results: list[dict[str, Any]] = []
            async for entry in await self._client.list_schedules():
                info = entry.info
                results.append(
                    {
                        "schedule_id": entry.id,
                        "workflow_type": getattr(info.action, "workflow", None),
                        "cron": (
                            info.spec.cron_expressions
                            if info.spec and info.spec.cron_expressions
                            else []
                        ),
                        "paused": entry.state.paused if entry.state else False,
                        "recent_actions": len(info.recent_actions) if info.recent_actions else 0,
                        "next_action_times": [
                            t.isoformat() for t in (info.next_action_times or [])
                        ],
                    }
                )
            return results
        except Exception as exc:
            raise TemporalRpcError(
                f"Failed to list schedules: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc
