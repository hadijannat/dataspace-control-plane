"""Gaia-X Compliance Service client.

Checks whether a Self-Description satisfies the Gaia-X Trust Framework
for a given federation. Federation profile is determined by config.federation_id.
"""
from __future__ import annotations

import logging

from dataspace_control_plane_adapters._shared.http import AsyncAdapterClient
from .config import GaiaXSettings
from .errors import GaiaXComplianceError

logger = logging.getLogger(__name__)


class GaiaXComplianceClient:
    """Client for the Gaia-X Compliance Service.

    Checks SD compliance and retrieves Compliance Credentials.
    No general policy evaluation — that belongs in core/domains/policies/.
    """

    def __init__(self, cfg: GaiaXSettings) -> None:
        self._cfg = cfg

    async def check_compliance(self, sd: dict) -> dict:
        """Submit a Self-Description for compliance verification.

        Args:
            sd: The Self-Description JSON-LD document.

        Returns:
            Dict with keys: compliant (bool), errors (list[str]).

        Raises:
            GaiaXComplianceError: If the compliance service is unavailable.
        """
        async with AsyncAdapterClient(
            str(self._cfg.compliance_service_url),
            timeout=self._cfg.request_timeout_s,
        ) as client:
            try:
                resp = await client.post(
                    "/api/v1/compliance/check",
                    json={"selfDescription": sd, "federationId": self._cfg.federation_id},
                )
                result = resp.json()
                return {
                    "compliant": result.get("compliant", False),
                    "errors": result.get("errors") or [],
                }
            except Exception as exc:
                raise GaiaXComplianceError(
                    f"Compliance check failed: {exc}"
                ) from exc

    async def get_compliance_credential(self, participant_did: str) -> str | None:
        """Fetch the Compliance Credential VC JWT for a participant, if available.

        Args:
            participant_did: DID of the participant.

        Returns:
            VC JWT string, or None if no compliance credential exists.
        """
        async with AsyncAdapterClient(
            str(self._cfg.compliance_service_url),
            timeout=self._cfg.request_timeout_s,
        ) as client:
            try:
                resp = await client.get(
                    f"/api/v1/compliance/credential?did={participant_did}"
                )
                result = resp.json()
                return result.get("verifiableCredential") or result.get("vc")
            except Exception:
                return None
