"""Unit tests for EdcConnectorAssetProbe and SSRF validation."""
from __future__ import annotations

import pytest

from dataspace_control_plane_adapters.dataspace.edc.ports_impl import _validate_probe_url


@pytest.mark.parametrize(
    "url",
    [
        "http://10.0.0.1/path",
        "http://10.255.255.255",
        "http://172.16.0.1",
        "http://172.31.255.255",
        "http://192.168.1.1",
        "http://127.0.0.1",
        "http://127.0.0.2/admin",
        "http://169.254.169.254/latest/meta-data",  # AWS IMDS
        "http://localhost",
        "http://localhost:8080",
        "ftp://external.example.com",
        "file:///etc/passwd",
        "http://",
        "http://::1",
    ],
)
def test_validate_probe_url_rejects_ssrf_targets(url: str) -> None:
    with pytest.raises(ValueError):
        _validate_probe_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://connector.example.com/health",
        "https://edc-provider.catena-x.net/api/v1/health",
        "http://partner-edc.example.org:8282",
        "https://connector.example.com:4443/path?q=1",
    ],
)
def test_validate_probe_url_allows_external_urls(url: str) -> None:
    # Should not raise
    _validate_probe_url(url)


def test_infer_procedure_type_handles_tenant_prefixed_workflow_id() -> None:
    from dataspace_control_plane_adapters.infrastructure.temporal_client.ports_impl import (
        _infer_procedure_type,
    )

    # Tenant-prefixed format: "{tenant_id}:{procedure_prefix}:{id}"
    assert _infer_procedure_type(None, "tenant-a:company-onboarding:wf-1") == "company-onboarding"
    assert _infer_procedure_type(None, "acme-corp:rotate-credentials:cred-42") == "machine-credential-rotation"
    assert _infer_procedure_type(None, "tenant-xyz:contract:neg-99") == "contract-negotiation"
    # Bare IDs (backward compatibility) still resolve
    assert _infer_procedure_type(None, "company-onboarding:wf-1") == "company-onboarding"
