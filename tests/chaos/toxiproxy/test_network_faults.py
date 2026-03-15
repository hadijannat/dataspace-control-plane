"""
Deterministic network fault injection tests using Toxiproxy.
"""
from __future__ import annotations

import base64
import time
import uuid

import pytest

pytestmark = pytest.mark.chaos


def test_postgres_latency_does_not_corrupt_data(
    create_rls_test_table,
    postgres_proxy,
    add_latency_toxic,
    proxied_postgres_superuser_conn,
) -> None:
    """
    Postgres traffic routed through Toxiproxy must still preserve data integrity under latency.
    """
    add_latency_toxic(postgres_proxy["name"], latency_ms=200)

    start = time.monotonic()
    cur = proxied_postgres_superuser_conn.cursor()
    test_value = f"chaos_test_{uuid.uuid4().hex}"
    cur.execute(
        """
        INSERT INTO rls_test_items (tenant_id, legal_entity_id, payload)
        VALUES ('chaos_tenant', '', %s)
        RETURNING id
        """,
        (test_value,),
    )
    row_id = cur.fetchone()[0]
    cur.execute("SELECT payload FROM rls_test_items WHERE id = %s", (row_id,))
    payload = cur.fetchone()[0]
    cur.close()
    elapsed = time.monotonic() - start

    assert payload == test_value
    assert elapsed >= 0.15


def test_postgres_connection_reset_triggers_recovery(
    postgres_proxy, add_reset_peer_toxic, proxied_postgres_url, toxiproxy_api_url
) -> None:
    """
    A reset_peer toxic must break proxied Postgres traffic until the toxic is removed,
    after which a new connection should succeed.
    """
    psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 required for chaos postgres tests")
    requests = pytest.importorskip("requests", reason="requests required for toxiproxy fixtures")

    toxic_name = f"reset_{postgres_proxy['name']}"
    add_reset_peer_toxic(postgres_proxy["name"], toxicity=1.0)

    with pytest.raises(Exception):
        conn = psycopg2.connect(proxied_postgres_url)
        try:
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
        finally:
            conn.close()

    resp = requests.delete(
        f"{toxiproxy_api_url}/proxies/{postgres_proxy['name']}/toxics/{toxic_name}",
        timeout=5,
    )
    resp.raise_for_status()

    conn = psycopg2.connect(proxied_postgres_url)
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        cur.close()
    finally:
        conn.close()


def test_vault_latency_degraded_signing(
    add_latency_toxic, proxied_vault_client, vault_transit_key, vault_proxy
) -> None:
    """
    Vault traffic routed through Toxiproxy must still succeed under latency and reflect the delay.
    """
    add_latency_toxic(vault_proxy["name"], latency_ms=500)

    payload = base64.b64encode(b"chaos latency signing test").decode()
    start = time.monotonic()
    result = proxied_vault_client.secrets.transit.sign_data(
        name=vault_transit_key,
        hash_input=payload,
        hash_algorithm="sha2-256",
    )
    elapsed = time.monotonic() - start

    assert "signature" in result.get("data", result)
    assert elapsed >= 0.4


def test_kafka_blackhole_detected(
    kafka_bootstrap, kafka_proxy, proxied_kafka_producer, toxiproxy_api_url
) -> None:
    """
    A Kafka blackhole toxic must prevent delivery through the proxied producer.
    """
    requests = pytest.importorskip("requests", reason="requests required for toxiproxy fixtures")
    confluent_kafka = pytest.importorskip("confluent_kafka", reason="confluent_kafka required")
    from confluent_kafka import Consumer

    resp = requests.post(
        f"{toxiproxy_api_url}/proxies/{kafka_proxy['name']}/toxics",
        json={
            "name": f"blackhole_{kafka_proxy['name']}",
            "type": "limit_data",
            "stream": "downstream",
            "toxicity": 1.0,
            "attributes": {"bytes": 0},
        },
        timeout=5,
    )
    resp.raise_for_status()

    test_topic = f"chaos-test-{uuid.uuid4().hex[:8]}"
    delivery_failed = False
    try:
        proxied_kafka_producer.produce(
            test_topic,
            key=b"chaos-key",
            value=b"this-should-not-arrive",
        )
        undelivered = proxied_kafka_producer.flush(timeout=2)
        delivery_failed = undelivered > 0
    except Exception:
        delivery_failed = True

    consumer = Consumer(
        {
            "bootstrap.servers": kafka_bootstrap,
            "group.id": f"chaos-consumer-{uuid.uuid4().hex[:8]}",
            "auto.offset.reset": "earliest",
        }
    )
    try:
        consumer.subscribe([test_topic])
        message = consumer.poll(timeout=2.0)
    finally:
        consumer.close()

    assert delivery_failed is True
    assert message is None
