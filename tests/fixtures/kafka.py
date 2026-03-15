"""
Kafka producer/consumer fixtures for integration tests.
Depends on kafka_container from fixtures/containers.py.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Bootstrap servers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def kafka_bootstrap(kafka_container) -> str:
    """Function-scoped bootstrap servers string for the running kafka_container."""
    return kafka_container.get_bootstrap_server()


# ---------------------------------------------------------------------------
# Producer
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def kafka_producer(kafka_bootstrap: str):
    """
    Function-scoped confluent_kafka.Producer.

    Flushes and closes on teardown. Skipped if confluent_kafka not installed.
    """
    confluent_kafka = pytest.importorskip("confluent_kafka", reason="confluent_kafka required")
    from confluent_kafka import Producer

    producer = Producer({"bootstrap.servers": kafka_bootstrap})
    yield producer
    producer.flush(timeout=10)


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def kafka_consumer(kafka_bootstrap: str, request: pytest.FixtureRequest):
    """
    Function-scoped confluent_kafka.Consumer subscribed to topics.

    Topics are read from request.param (default: ['test-topic']).
    Closes on teardown. Skipped if confluent_kafka not installed.
    """
    confluent_kafka = pytest.importorskip("confluent_kafka", reason="confluent_kafka required")
    from confluent_kafka import Consumer

    topics = getattr(request, "param", ["test-topic"])
    consumer = Consumer(
        {
            "bootstrap.servers": kafka_bootstrap,
            "group.id": "test-consumer-group",
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe(topics)
    yield consumer
    consumer.close()
