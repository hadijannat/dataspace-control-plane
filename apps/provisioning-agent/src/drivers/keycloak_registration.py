"""
Keycloak Client Registration Service driver.
Uses OIDC client registration (RFC 7591) rather than Admin REST for
standards-aligned registration flows. Admin REST is preferred for realm/role management;
this driver handles install-profile and OIDC-native client registration.
"""
from __future__ import annotations
import httpx
import structlog

logger = structlog.get_logger(__name__)


class KeycloakRegistrationDriver:
    """
    Thin wrapper around Keycloak's Client Registration Service.
    Authentication uses an initial_access_token (provided by admin) or a registration_access_token.
    """

    def __init__(self, base_url: str, realm: str, initial_access_token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.realm = realm
        self._initial_token = initial_access_token
        self._reg_url = f"{self.base_url}/auth/realms/{realm}/clients-registrations"

    def _headers(self, registration_token: str | None = None) -> dict:
        token = registration_token or self._initial_token
        if not token:
            return {"Content-Type": "application/json"}
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def register_client_oidc(self, client_metadata: dict, registration_token: str | None = None) -> dict:
        """
        Register a new OIDC client using RFC 7591 client registration.
        Returns the registered client metadata including registration_access_token.
        """
        url = f"{self._reg_url}/openid-connect"
        with httpx.Client() as client:
            resp = client.post(url, json=client_metadata, headers=self._headers(registration_token))
        if resp.status_code == 201:
            result = resp.json()
            logger.info("kc_registration.client_registered", client_id=result.get("client_id"))
            return result
        logger.error("kc_registration.failed", status=resp.status_code, detail=resp.text)
        resp.raise_for_status()
        return {}

    def get_client_oidc(self, client_id: str, registration_access_token: str) -> dict | None:
        """Read a registered OIDC client by client_id using its registration_access_token."""
        url = f"{self._reg_url}/openid-connect/{client_id}"
        with httpx.Client() as client:
            resp = client.get(url, headers=self._headers(registration_access_token))
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def update_client_oidc(self, client_id: str, registration_access_token: str, metadata: dict) -> dict:
        """Update a registered OIDC client."""
        url = f"{self._reg_url}/openid-connect/{client_id}"
        with httpx.Client() as client:
            resp = client.put(url, json=metadata, headers=self._headers(registration_access_token))
        resp.raise_for_status()
        return resp.json()

    def delete_client_oidc(self, client_id: str, registration_access_token: str) -> None:
        """Delete a registered OIDC client. Idempotent on 404."""
        url = f"{self._reg_url}/openid-connect/{client_id}"
        with httpx.Client() as client:
            resp = client.delete(url, headers=self._headers(registration_access_token))
        if resp.status_code == 404:
            return
        resp.raise_for_status()
        logger.info("kc_registration.client_deleted", client_id=client_id)
