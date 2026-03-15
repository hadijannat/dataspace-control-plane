"""
Toxiproxy HTTP API helpers for chaos suites.
Depends on toxiproxy_container from fixtures/containers.py.
"""
from __future__ import annotations

from typing import Any, Callable
from urllib.parse import urlparse, urlunparse

import pytest


def _requests():
    return pytest.importorskip("requests", reason="requests required for toxiproxy fixtures")


def _docker_reachable_host(host: str) -> str:
    if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return "host.docker.internal"
    return host


def _upstream_for_container(container, internal_port: int) -> str:
    host = _docker_reachable_host(container.get_container_host_ip())
    port = container.get_exposed_port(internal_port)
    return f"{host}:{port}"


def _upstream_for_host_endpoint(endpoint: str) -> str:
    host, port = endpoint.split(":", 1)
    return f"{_docker_reachable_host(host)}:{port}"


# ---------------------------------------------------------------------------
# API URL and proxy factory
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def toxiproxy_api_url(toxiproxy_container) -> str:
    """Function-scoped Toxiproxy HTTP API base URL."""
    _container, api_url = toxiproxy_container
    return api_url


@pytest.fixture(scope="function")
def toxiproxy_proxy_factory(toxiproxy_container, toxiproxy_api_url: str):
    """
    Create named Toxiproxy proxies and expose client connection endpoints.
    """
    requests = _requests()
    container, _api_url = toxiproxy_container
    available_ports = list(range(18000, 18011))
    created: list[str] = []

    def create(*, name: str, upstream: str) -> dict[str, Any]:
        if not available_ports:
            raise RuntimeError("Exhausted exposed Toxiproxy ports for this test")

        internal_port = available_ports.pop(0)
        listen = f"0.0.0.0:{internal_port}"
        resp = requests.post(
            f"{toxiproxy_api_url}/proxies",
            json={"name": name, "upstream": upstream, "listen": listen, "enabled": True},
            timeout=5,
        )
        resp.raise_for_status()
        created.append(name)

        return {
            "name": name,
            "listen": listen,
            "upstream": upstream,
            "api_url": toxiproxy_api_url,
            "client_host": container.get_container_host_ip(),
            "client_port": int(container.get_exposed_port(internal_port)),
            "client_endpoint": f"{container.get_container_host_ip()}:{container.get_exposed_port(internal_port)}",
        }

    yield create

    for name in reversed(created):
        try:
            requests.delete(f"{toxiproxy_api_url}/proxies/{name}", timeout=5)
        except Exception:
            pass


@pytest.fixture(scope="function")
def toxiproxy_proxy(toxiproxy_proxy_factory, request: pytest.FixtureRequest) -> dict[str, Any]:
    """
    Backwards-compatible generic proxy fixture.
    """
    proxy_name = getattr(request, "param", "test-proxy")
    marker = request.node.get_closest_marker("toxiproxy_upstream")
    upstream = marker.args[0] if marker else "host.docker.internal:5432"
    return toxiproxy_proxy_factory(name=proxy_name, upstream=upstream)


# ---------------------------------------------------------------------------
# Service-specific proxies and clients
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def postgres_proxy(postgres_container, toxiproxy_proxy_factory):
    return toxiproxy_proxy_factory(
        name="postgres-proxy",
        upstream=_upstream_for_container(postgres_container, 5432),
    )


@pytest.fixture(scope="function")
def proxied_postgres_url(postgres_container, postgres_proxy) -> str:
    parsed = urlparse(postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql://"))
    proxied = parsed._replace(netloc=f"{parsed.username}:{parsed.password}@{postgres_proxy['client_host']}:{postgres_proxy['client_port']}")
    return urlunparse(proxied)


@pytest.fixture(scope="function")
def proxied_postgres_superuser_conn(proxied_postgres_url: str):
    psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 required for proxied postgres fixtures")
    conn = psycopg2.connect(proxied_postgres_url)
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def vault_proxy(vault_container, toxiproxy_proxy_factory):
    return toxiproxy_proxy_factory(
        name="vault-proxy",
        upstream=_upstream_for_container(vault_container, 8200),
    )


@pytest.fixture(scope="function")
def proxied_vault_client(vault_proxy):
    hvac = pytest.importorskip("hvac", reason="hvac required for proxied vault fixtures")
    client = hvac.Client(
        url=f"http://{vault_proxy['client_host']}:{vault_proxy['client_port']}",
        token="dev-root-token",
    )
    assert client.is_authenticated(), "Vault client authentication failed through Toxiproxy"
    return client


@pytest.fixture(scope="function")
def kafka_proxy(kafka_bootstrap: str, toxiproxy_proxy_factory):
    return toxiproxy_proxy_factory(
        name="kafka-proxy",
        upstream=_upstream_for_host_endpoint(kafka_bootstrap),
    )


@pytest.fixture(scope="function")
def proxied_kafka_bootstrap(kafka_proxy) -> str:
    return f"{kafka_proxy['client_host']}:{kafka_proxy['client_port']}"


@pytest.fixture(scope="function")
def proxied_kafka_producer(proxied_kafka_bootstrap: str):
    confluent_kafka = pytest.importorskip("confluent_kafka", reason="confluent_kafka required")
    from confluent_kafka import Producer

    producer = Producer({"bootstrap.servers": proxied_kafka_bootstrap})
    yield producer
    producer.flush(timeout=10)


# ---------------------------------------------------------------------------
# Toxic helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def add_latency_toxic(toxiproxy_api_url: str) -> Callable[[str, int, int], Any]:
    """
    Returns callable: add(proxy_name, latency_ms, jitter_ms=0) -> Response.
    """
    requests = _requests()

    def add(proxy_name: str, latency_ms: int, jitter_ms: int = 0):
        resp = requests.post(
            f"{toxiproxy_api_url}/proxies/{proxy_name}/toxics",
            json={
                "name": f"latency_{proxy_name}",
                "type": "latency",
                "stream": "downstream",
                "toxicity": 1.0,
                "attributes": {"latency": latency_ms, "jitter": jitter_ms},
            },
            timeout=5,
        )
        resp.raise_for_status()
        return resp

    return add


@pytest.fixture(scope="function")
def add_reset_peer_toxic(toxiproxy_api_url: str) -> Callable[[str, float], Any]:
    """
    Returns callable: add(proxy_name, toxicity=1.0) -> Response.
    """
    requests = _requests()

    def add(proxy_name: str, toxicity: float = 1.0):
        resp = requests.post(
            f"{toxiproxy_api_url}/proxies/{proxy_name}/toxics",
            json={
                "name": f"reset_{proxy_name}",
                "type": "reset_peer",
                "stream": "downstream",
                "toxicity": toxicity,
                "attributes": {"timeout": 0},
            },
            timeout=5,
        )
        resp.raise_for_status()
        return resp

    return add
