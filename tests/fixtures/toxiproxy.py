"""
Toxiproxy HTTP API helpers for chaos suite.
Depends on toxiproxy_container from fixtures/containers.py.
"""
from __future__ import annotations

from typing import Any, Callable

import pytest


# ---------------------------------------------------------------------------
# API URL
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def toxiproxy_api_url(toxiproxy_container) -> str:
    """Function-scoped Toxiproxy HTTP API base URL."""
    _container, api_url = toxiproxy_container
    return api_url


# ---------------------------------------------------------------------------
# Proxy lifecycle
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def toxiproxy_proxy(toxiproxy_api_url: str, request: pytest.FixtureRequest) -> dict:
    """
    Function-scoped fixture that creates a named Toxiproxy proxy.

    Proxy name is read from request.param (default: 'test-proxy').
    Upstream is read from marker or defaults to 'localhost:5432'.
    Listen address: '0.0.0.0:18000'.

    Yields dict: {name, listen, upstream, api_url}.
    Deletes proxy on teardown.
    Skipped if requests is not installed.
    """
    requests = pytest.importorskip("requests", reason="requests required for toxiproxy fixtures")

    proxy_name = getattr(request, "param", "test-proxy")
    upstream = "localhost:5432"

    marker = request.node.get_closest_marker("toxiproxy_upstream")
    if marker:
        upstream = marker.args[0]

    listen = "0.0.0.0:18000"

    resp = requests.post(
        f"{toxiproxy_api_url}/proxies",
        json={
            "name": proxy_name,
            "upstream": upstream,
            "listen": listen,
            "enabled": True,
        },
        timeout=5,
    )
    resp.raise_for_status()

    proxy_info = {"name": proxy_name, "listen": listen, "upstream": upstream, "api_url": toxiproxy_api_url}
    yield proxy_info

    # Teardown: delete proxy
    try:
        requests.delete(f"{toxiproxy_api_url}/proxies/{proxy_name}", timeout=5)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Latency toxic factory
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def add_latency_toxic(toxiproxy_api_url: str) -> Callable[[str, int, int], Any]:
    """
    Function-scoped fixture factory.

    Returns callable: add(proxy_name, latency_ms, jitter_ms=0) → requests.Response.
    Posts a 'latency' toxic via the Toxiproxy API.
    Skipped if requests is not installed.
    """
    requests = pytest.importorskip("requests", reason="requests required for toxiproxy fixtures")

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


# ---------------------------------------------------------------------------
# Reset-peer toxic factory
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def add_reset_peer_toxic(toxiproxy_api_url: str) -> Callable[[str, float], Any]:
    """
    Function-scoped fixture factory.

    Returns callable: add(proxy_name, toxicity=1.0) → requests.Response.
    Posts a 'reset_peer' toxic via the Toxiproxy API.
    Skipped if requests is not installed.
    """
    requests = pytest.importorskip("requests", reason="requests required for toxiproxy fixtures")

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
