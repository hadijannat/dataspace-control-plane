---
title: "Authentication Guide"
summary: "Human operator and service-to-service authentication flows, token structure, required roles, and code examples."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Authentication Guide

All control-api endpoints under `/api/v1/` require a Bearer JWT issued by the tenant's Keycloak realm. The authentication flow differs between human operators (browser sessions) and machine service accounts (automated API calls).

## Human Operator Authentication (Authorization Code + PKCE)

Human operators authenticate via the Keycloak Authorization Code flow with PKCE (Proof Key for Code Exchange). The web-console handles this flow automatically using the Keycloak JavaScript adapter.

**Flow summary:**

1. Browser navigates to the web-console.
2. Web-console redirects to `https://keycloak/realms/{realm}/protocol/openid-connect/auth?client_id=web-console&response_type=code&scope=openid&code_challenge={challenge}&code_challenge_method=S256&redirect_uri={callback}`.
3. Operator authenticates with Keycloak (username/password + MFA if enforced).
4. Keycloak redirects to the callback URL with `?code={authorization_code}`.
5. Web-console exchanges the code: `POST https://keycloak/realms/{realm}/protocol/openid-connect/token` with `grant_type=authorization_code&code={code}&code_verifier={verifier}`.
6. Keycloak returns `{"access_token": "...", "refresh_token": "...", "expires_in": 300}`.
7. Web-console includes the access token as `Authorization: Bearer {access_token}` on every API call.

**Token TTL**: 5 minutes for human tokens. Use the `refresh_token` (24-hour TTL) to obtain new access tokens silently.

## Service-to-Service Authentication (client_credentials)

Machine services authenticate using the OAuth 2.0 `client_credentials` grant. The `client_id` and `client_secret` are Keycloak service account credentials provisioned during company onboarding and stored in Vault.

**Token request:**

```http
POST https://keycloak/realms/{realm}/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id={service_client_id}&
client_secret={service_client_secret}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900,
  "token_type": "Bearer"
}
```

**Token TTL**: 15 minutes for machine tokens. Cache the token and refresh 60 seconds before expiry to avoid failed requests due to clock skew.

**Python example:**

```python
import httpx
import time

class KeycloakTokenCache:
    def __init__(self, realm_url: str, client_id: str, client_secret: str):
        self.token_url = f"{realm_url}/protocol/openid-connect/token"
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._expires_at: float = 0.0

    async def get_token(self) -> str:
        if self._token and time.monotonic() < self._expires_at - 60:
            return self._token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()
            self._token = data["access_token"]
            self._expires_at = time.monotonic() + data["expires_in"]
            return self._token

    async def get_auth_header(self) -> dict[str, str]:
        token = await self.get_token()
        return {"Authorization": f"Bearer {token}"}
```

## Token Structure and Claims

All JWTs issued by Keycloak for the platform contain the following claims:

| Claim | Type | Description |
|-------|------|-------------|
| `sub` | string (UUID) | Subject — the Keycloak user ID or service account ID |
| `azp` | string | Authorized party — the client ID that requested the token |
| `iss` | string (URI) | Issuer — the Keycloak realm URL: `https://keycloak/realms/{realm}` |
| `exp` | integer (Unix ts) | Expiration timestamp |
| `iat` | integer (Unix ts) | Issued-at timestamp |
| `realm_access.roles` | string[] | Realm-level roles assigned to this principal |
| `resource_access.control-api.roles` | string[] | control-api client-level roles |
| `tenant_id` | string | Custom claim: the platform tenant ID (set by Keycloak mapper) |

**Example decoded payload:**

```json
{
  "sub": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "azp": "web-console",
  "iss": "https://keycloak/realms/tenant-BPNL000000000001",
  "exp": 1710000300,
  "iat": 1710000000,
  "realm_access": {
    "roles": ["operator", "offline_access"]
  },
  "resource_access": {
    "control-api": {
      "roles": ["operator"]
    }
  },
  "tenant_id": "tenant-BPNL000000000001"
}
```

## Required Roles

The control-api enforces role-based access control via Keycloak roles validated in the JWT:

| Role | Grant | Permitted operations |
|------|-------|---------------------|
| `operator` | Human operators, provisioning-agent | All mutation endpoints: POST/PATCH/DELETE on companies, negotiations, passports |
| `viewer` | Human operators (read-only) | All GET endpoints only |
| `service-account` | Machine services (temporal-workers, edc-extension) | Usage event recording, internal status updates |
| `admin` | Platform administrators only | Company suspension, tenant deletion |

Requests with insufficient roles receive `403 Forbidden` with a Problem Details body (`/errors/authorization-denied`).

## JWKS Endpoint

The control-api validates tokens by fetching the public key set from Keycloak's JWKS endpoint:

```
GET https://keycloak/realms/{realm}/protocol/openid-connect/certs
```

The JWKS URL is configured via the `KEYCLOAK_JWKS_URL` environment variable. The control-api caches the JWKS and refreshes it on key rotation (detected by `kid` mismatch in incoming JWTs).

## MFA Enforcement

For human operators in production, MFA is enforced at the Keycloak realm level. Operators must register a TOTP authenticator (RFC 6238) on first login. MFA is not required for machine service accounts.
