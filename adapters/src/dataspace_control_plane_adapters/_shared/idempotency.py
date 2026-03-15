"""Idempotency helpers for adapter writes.

Used by Kafka producer wrappers, webhook emitters, and any adapter call that
must not duplicate side effects on retry.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def deterministic_key(namespace: str, *parts: Any) -> str:
    """Produce a stable, collision-resistant idempotency key from structured parts.

    The key is a hex SHA-256 digest of the JSON-serialised parts list, prefixed
    with the namespace. Safe for use as a Kafka message key, Temporal workflow ID
    suffix, or database idempotency column value.
    """
    payload = json.dumps([namespace, *[str(p) for p in parts]], sort_keys=True)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return f"{namespace}:{digest[:32]}"


class IdempotentSet:
    """In-memory deduplication set for short-lived operation windows.

    For durable deduplication across process restarts, use the outbox table
    in infrastructure/postgres/.
    """

    def __init__(self, max_size: int = 10_000) -> None:
        self._seen: set[str] = set()
        self._max_size = max_size

    def is_seen(self, key: str) -> bool:
        return key in self._seen

    def mark(self, key: str) -> None:
        if len(self._seen) >= self._max_size:
            # Evict oldest half — simple FIFO approximation for in-memory use.
            half = list(self._seen)[: self._max_size // 2]
            for k in half:
                self._seen.discard(k)
        self._seen.add(key)
