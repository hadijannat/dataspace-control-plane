from __future__ import annotations

from datetime import datetime, timezone

import pytest

from dataspace_control_plane_adapters._shared.health import HealthStatus
from dataspace_control_plane_adapters.dataspace.dcp import api as dcp_api
from dataspace_control_plane_adapters.dataspace.dcp.health import DcpHealthProbe
from dataspace_control_plane_adapters.dataspace.dcp.presentation_mapper import (
    map_verification_result,
)
from dataspace_control_plane_adapters.dataspace.dcp import ports_impl as dcp_ports
from dataspace_control_plane_adapters.dataspace.dcp.config import DcpSettings
from dataspace_control_plane_core.canonical_models.enums import CredentialFormat
from dataspace_control_plane_core.canonical_models.identity import (
    CredentialEnvelope,
    DidUri,
    PresentationEnvelope,
)
from dataspace_control_plane_core.domains.machine_trust.model.enums import (
    VerificationResult,
)


def _settings() -> DcpSettings:
    return DcpSettings(
        credential_service_url="https://credential-service.example.com",
        issuer_service_url="https://issuer.example.com",
        trust_anchor_urls=[
            "https://gaia-x.example.com/trust-anchor",
            "https://catena-x.example.com/trust-anchor",
        ],
    )


def _presentation() -> PresentationEnvelope:
    return PresentationEnvelope(
        id="jwt-vp-token",
        holder_did=DidUri(uri="did:web:holder.example.com"),
        credentials=[
            CredentialEnvelope(
                id="vc-1",
                format=CredentialFormat.JWT_VC,
                issuer_did=DidUri(uri="did:web:issuer.example.com"),
                subject_did=DidUri(uri="did:web:holder.example.com"),
                type_labels=["VerifiableCredential", "MembershipCredential"],
                issued_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            )
        ],
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


class _FakeVerifierClient:
    def __init__(self, *_args, **_kwargs) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    async def __aenter__(self) -> "_FakeVerifierClient":
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def verify_presentation(
        self,
        presentation_jwt: str,
        required_types: list[str],
    ) -> dict[str, object]:
        self.calls.append((presentation_jwt, required_types))
        return {"valid": False, "error": "issuer trust anchor missing"}


@pytest.mark.asyncio
async def test_presentation_verifier_returns_core_verification_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(dcp_ports, "DcpVerifierClient", _FakeVerifierClient)

    verifier = dcp_ports.DcpPresentationVerifier(_settings())
    result = await verifier.verify(_presentation())

    assert result is VerificationResult.UNTRUSTED_ISSUER


def test_map_verification_result_normalizes_dcp_errors() -> None:
    assert (
        map_verification_result({"valid": False, "error": "signature invalid"})
        is VerificationResult.INVALID_SIGNATURE
    )
    assert map_verification_result({"valid": True}) is VerificationResult.VALID


def test_public_api_hides_si_token_helpers() -> None:
    assert {"SiTokenBuilder", "decode_si_token"}.isdisjoint(dcp_api.__all__)


@pytest.mark.asyncio
async def test_dcp_health_probe_reports_trust_anchor_configuration() -> None:
    probe = DcpHealthProbe(_settings())

    report = await probe.check()
    descriptor = probe.capability_descriptor()

    assert report.status is HealthStatus.OK
    assert report.details["trust_anchor_count"] == 2
    assert descriptor["trust_anchor_count"] == 2


# ---------------------------------------------------------------------------
# map_verification_result — all error branches
# ---------------------------------------------------------------------------

def test_map_verification_result_maps_revoked_error() -> None:
    from dataspace_control_plane_adapters.dataspace.dcp.presentation_mapper import (
        map_verification_result,
    )
    from dataspace_control_plane_core.domains.machine_trust.model.enums import VerificationResult

    assert (
        map_verification_result({"valid": False, "error": "credential is revoked"})
        is VerificationResult.REVOKED
    )


def test_map_verification_result_maps_expired_error() -> None:
    from dataspace_control_plane_adapters.dataspace.dcp.presentation_mapper import (
        map_verification_result,
    )
    from dataspace_control_plane_core.domains.machine_trust.model.enums import VerificationResult

    assert (
        map_verification_result({"valid": False, "error": "VC has expired"})
        is VerificationResult.EXPIRED
    )


def test_map_verification_result_returns_unknown_for_unrecognized_error() -> None:
    from dataspace_control_plane_adapters.dataspace.dcp.presentation_mapper import (
        map_verification_result,
    )
    from dataspace_control_plane_core.domains.machine_trust.model.enums import VerificationResult

    assert (
        map_verification_result({"valid": False, "error": "some completely unknown error"})
        is VerificationResult.UNKNOWN
    )


# ---------------------------------------------------------------------------
# DcpTrustAnchorResolver — scope filtering and URL-to-DID conversion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dcp_trust_anchor_resolver_filters_by_scope() -> None:
    resolver = dcp_ports.DcpTrustAnchorResolver(_settings())
    anchors = await resolver.list_active("gaia-x")

    # Only the gaia-x URL matches; catena-x URL should be filtered out
    assert len(anchors) == 1
    assert "gaia-x" in anchors[0].did.uri


@pytest.mark.asyncio
async def test_dcp_trust_anchor_resolver_returns_all_when_no_match() -> None:
    resolver = dcp_ports.DcpTrustAnchorResolver(_settings())
    anchors = await resolver.list_active("completely-unknown-scope")

    # No URL matches scope → entire configured list returned
    assert len(anchors) == 2


def test_url_to_did_web_strips_https_prefix_and_path() -> None:
    from dataspace_control_plane_adapters.dataspace.dcp.ports_impl import _url_to_did_web

    assert _url_to_did_web("https://ta.example.com/trust") == "did:web:ta.example.com"
    assert _url_to_did_web("https://ta.example.com") == "did:web:ta.example.com"


def test_url_to_did_web_encodes_port() -> None:
    from dataspace_control_plane_adapters.dataspace.dcp.ports_impl import _url_to_did_web

    # Port remains in the host segment (did:web encoding uses %3A in resolution,
    # but _url_to_did_web produces the raw host:port string)
    result = _url_to_did_web("https://ta.example.com:8443")
    assert result == "did:web:ta.example.com:8443"


def test_select_trust_anchor_urls_returns_all_for_empty_scope() -> None:
    from dataspace_control_plane_adapters.dataspace.dcp.ports_impl import _select_trust_anchor_urls

    urls = ["https://a.com", "https://b.com"]
    assert _select_trust_anchor_urls(urls, "") == urls
