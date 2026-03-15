"""
Testcontainers fixtures for integration and chaos suites.
Requires Docker and the testcontainers Python library.
Import these fixtures in integration conftest.py files via pytest_plugins.

All containers are session-scoped and only started when --live-services is passed.
"""
from __future__ import annotations

import time

import pytest


def _require_live_services(request) -> None:
    """Skip if --live-services is not passed."""
    live = request.config.getoption("--live-services", default=False) or request.config.getoption(
        "--containers", default=False
    )
    if not live:
        pytest.skip("Pass --live-services to start containers")


def _docker_available() -> bool:
    """Return True if the Docker daemon is reachable."""
    try:
        import docker

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


def _wait_for_http(url: str, timeout: float = 60.0, interval: float = 2.0) -> bool:
    """Poll url until it returns any response or timeout expires."""
    import urllib.request

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=3)
            return True
        except Exception:
            time.sleep(interval)
    return False


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_container(request):
    """
    Starts a postgres:16-alpine container for the test session.

    Yields the running container. Stopped on teardown.
    Skipped if --live-services is not passed, testcontainers is missing, or Docker unavailable.
    """
    _require_live_services(request)
    pytest.importorskip("testcontainers", reason="testcontainers required for postgres_container")
    if not _docker_available():
        pytest.skip("Docker not available — skipping postgres_container")

    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer(
        image="postgres:16-alpine",
        dbname="testdb",
        username="testuser",
        password="testpass",
    )
    container.start()
    try:
        yield container
    finally:
        container.stop()


# ---------------------------------------------------------------------------
# Keycloak
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def keycloak_container(request):
    """
    Starts quay.io/keycloak/keycloak:24.0 in dev mode.

    Waits for /realms/master to respond before yielding.
    Skipped if --live-services is not passed, testcontainers is missing, or Docker unavailable.
    """
    _require_live_services(request)
    pytest.importorskip("testcontainers", reason="testcontainers required for keycloak_container")
    if not _docker_available():
        pytest.skip("Docker not available — skipping keycloak_container")

    from testcontainers.core.container import DockerContainer

    container = (
        DockerContainer("quay.io/keycloak/keycloak:24.0")
        .with_command("start-dev")
        .with_env("KEYCLOAK_ADMIN", "admin")
        .with_env("KEYCLOAK_ADMIN_PASSWORD", "admin")
        .with_exposed_ports(8080)
    )
    container.start()
    try:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8080)
        readiness_url = f"http://{host}:{port}/realms/master"
        if not _wait_for_http(readiness_url, timeout=120.0):
            pytest.skip("Keycloak did not become ready in time")
        yield container
    finally:
        container.stop()


# ---------------------------------------------------------------------------
# HashiCorp Vault
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def vault_container(request):
    """
    Starts hashicorp/vault:1.17 in dev mode with a known root token.

    Skipped if --live-services is not passed, testcontainers is missing, or Docker unavailable.
    """
    _require_live_services(request)
    pytest.importorskip("testcontainers", reason="testcontainers required for vault_container")
    if not _docker_available():
        pytest.skip("Docker not available — skipping vault_container")

    from testcontainers.core.container import DockerContainer

    container = (
        DockerContainer("hashicorp/vault:1.17")
        .with_env("VAULT_DEV_ROOT_TOKEN_ID", "dev-root-token")
        .with_env("VAULT_DEV_LISTEN_ADDRESS", "0.0.0.0:8200")
        .with_exposed_ports(8200)
    )
    container.start()
    try:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(8200)
        ready_url = f"http://{host}:{port}/v1/sys/health"
        if not _wait_for_http(ready_url, timeout=60.0):
            pytest.skip("Vault did not become ready in time")
        yield container
    finally:
        container.stop()


# ---------------------------------------------------------------------------
# Kafka
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def kafka_container(request):
    """
    Starts confluentinc/cp-kafka:7.6.1 in single-node KRaft-compatible mode.

    Skipped if --live-services is not passed, testcontainers is missing, or Docker unavailable.
    """
    _require_live_services(request)
    pytest.importorskip("testcontainers", reason="testcontainers required for kafka_container")
    if not _docker_available():
        pytest.skip("Docker not available — skipping kafka_container")

    from testcontainers.kafka import KafkaContainer

    container = KafkaContainer(image="confluentinc/cp-kafka:7.6.1")
    container.start()
    try:
        yield container
    finally:
        container.stop()


# ---------------------------------------------------------------------------
# Toxiproxy
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def toxiproxy_container(request):
    """
    Starts ghcr.io/shopify/toxiproxy:2.9.0.

    Exposes the API on port 8474 and proxy ports 18000-18010.
    Yields tuple (container, api_base_url).
    Skipped if --live-services is not passed, testcontainers is missing, or Docker unavailable.
    """
    _require_live_services(request)
    pytest.importorskip("testcontainers", reason="testcontainers required for toxiproxy_container")
    if not _docker_available():
        pytest.skip("Docker not available — skipping toxiproxy_container")

    from testcontainers.core.container import DockerContainer

    container = DockerContainer("ghcr.io/shopify/toxiproxy:2.9.0").with_exposed_ports(
        8474, *range(18000, 18011)
    )
    container.start()
    try:
        host = container.get_container_host_ip()
        api_port = container.get_exposed_port(8474)
        api_url = f"http://{host}:{api_port}"
        if not _wait_for_http(f"{api_url}/version", timeout=30.0):
            pytest.skip("Toxiproxy did not become ready in time")
        yield container, api_url
    finally:
        container.stop()
