"""Kafka event ingestion and normalized event publishing adapter.

Provides an idempotent producer (enable.idempotence=True by default, enforcing
acks=all, retries>0, max.in.flight.requests.per.connection<=5), a consumer
wrapper, DLQ support, and envelope serde.
"""
from __future__ import annotations
