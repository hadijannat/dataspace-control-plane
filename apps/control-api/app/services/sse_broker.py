"""
In-process SSE broker. Publishes workflow status events to subscribed HTTP connections.
For production with multiple API replicas, replace with Redis pub/sub or similar.
"""
import asyncio
from collections import defaultdict
from typing import AsyncIterator
import structlog

logger = structlog.get_logger(__name__)


class SSEBroker:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    async def publish(self, channel: str, event: str) -> None:
        queues = self._subscribers.get(channel, [])
        for q in queues:
            await q.put(event)

    async def subscribe(self, channel: str) -> AsyncIterator[str]:
        q: asyncio.Queue[str] = asyncio.Queue()
        self._subscribers[channel].append(q)
        try:
            while True:
                event = await q.get()
                if event == "__CLOSE__":
                    break
                yield event
        finally:
            self._subscribers[channel].remove(q)

    async def close(self) -> None:
        for channel, queues in self._subscribers.items():
            for q in queues:
                await q.put("__CLOSE__")
