from app.main import app


def test_openapi_exposes_operator_and_stream_paths():
    schema = app.openapi()

    assert "/api/v1/operator/procedures/start" in schema["paths"]
    assert "/api/v1/operator/procedures/" in schema["paths"]
    assert "/api/v1/operator/procedures/{workflow_id}" in schema["paths"]
    assert "/api/v1/operator/tenants/" in schema["paths"]
    assert "/api/v1/operator/tenants/{tenant_id}" in schema["paths"]
    assert "/api/v1/public/procedures/start" in schema["paths"]
    assert "/api/v1/public/procedures/{workflow_id}" in schema["paths"]
    assert "/api/v1/streams/tickets" in schema["paths"]
    assert "/api/v1/streams/workflows/{workflow_id}" in schema["paths"]
    assert "/api/v1/webhooks/management" not in schema["paths"]
