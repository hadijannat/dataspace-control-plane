"""
Idempotency key store.

Backed by an in-process dict for the current scaffold. The interface is
designed to be swapped for a Redis-backed implementation without touching
callers: ``check`` / ``store`` are async, and the class carries a configurable
TTL. Keys that have exceeded their TTL are evicted lazily on read.

Contract
--------
- ``check(key)`` — return the previously stored result if the key exists and
  has not expired; otherwise return ``None``.
- ``store(key, result)`` — persist the result under the key with the current
  timestamp so it can be served on duplicate requests within the TTL window.
"""
import time
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class IdempotencyStore:
    """
    In-process idempotency store with TTL-based eviction.

    Each stored entry is a ``dict`` holding the caller's ``result`` alongside
    the ``stored_at`` epoch timestamp. On read, entries older than ``ttl_seconds``
    are treated as expired and evicted, returning ``None`` to the caller.

    For multi-replica deployments replace this class with a Redis-backed
    implementation that exposes the same ``check`` / ``store`` async interface.
    """

    def __init__(self, ttl_seconds: int = 86400) -> None:
        """
        Parameters
        ----------
        ttl_seconds:
            How long (in seconds) a stored result is considered valid.
            Default is 24 hours.
        """
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, dict[str, Any]] = {}

    async def check(self, key: str) -> dict | None:
        """
        Return the stored result for *key* if it exists and has not expired.

        Expired entries are evicted from the in-process dict on access.

        Parameters
        ----------
        key:
            The idempotency key provided by the caller.

        Returns
        -------
        dict or None
            The original result dict, or ``None`` if the key is unknown or expired.
        """
        entry = self._store.get(key)
        if entry is None:
            return None
        age = time.monotonic() - entry["stored_at"]
        if age > self.ttl_seconds:
            logger.debug("idempotency.evict_expired", key=key, age_seconds=int(age))
            del self._store[key]
            return None
        logger.debug("idempotency.cache_hit", key=key, age_seconds=int(age))
        return entry["result"]

    async def store(self, key: str, result: dict) -> None:
        """
        Persist *result* under *key* with the current monotonic timestamp.

        Subsequent calls to ``check(key)`` within the TTL window will return
        *result* verbatim, allowing duplicate HTTP requests to receive the
        same response as the first.

        Parameters
        ----------
        key:
            The idempotency key provided by the caller.
        result:
            The result dict to cache. Must be JSON-serialisable for future
            Redis portability.
        """
        self._store[key] = {
            "result": result,
            "stored_at": time.monotonic(),
        }
        logger.debug("idempotency.stored", key=key)
