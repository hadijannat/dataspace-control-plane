from src.health import ProbeState, render_probe_response


def test_liveness_is_available_before_workers_are_ready():
    status_code, payload = render_probe_response("/health/live", ProbeState())

    assert status_code == 200
    assert payload["status"] == "ok"


def test_readiness_reflects_worker_startup_state():
    cold_status, cold_payload = render_probe_response("/health/ready", ProbeState())
    warm_status, warm_payload = render_probe_response(
        "/health/ready",
        ProbeState(
            temporal_connected=True,
            registry_verified=True,
            workers_started=True,
        ),
    )

    assert cold_status == 503
    assert cold_payload["status"] == "degraded"
    assert warm_status == 200
    assert warm_payload["status"] == "ok"
