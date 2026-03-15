"""OIDC access token verifier backed by python-jose and JwksCache.

Satisfies the verification side of the Keycloak adapter.  The decoded claims
dict is returned to ``principal_mapper.py`` for conversion to ``OperatorPrincipal``.

Algorithm support: RS256 (the Keycloak default).  If the realm is configured
for ES256 or RS512, ``algorithms`` can be extended in ``KeycloakSettings``.

Retry on unknown kid
--------------------
If the token carries a ``kid`` not present in the cache (key rotation), the
verifier refreshes the JWKS once and retries.  A second failure raises
``KeycloakTokenInvalidError``.

Usage::

    verifier = OidcVerifier(settings, jwks_cache)
    claims = await verifier.verify(access_token_string)
    # → dict with 'sub', 'email', 'realm_access', 'tenant', etc.
"""
from __future__ import annotations

import logging
from typing import Any

from dataspace_control_plane_adapters.infrastructure.keycloak.config import KeycloakSettings
from dataspace_control_plane_adapters.infrastructure.keycloak.errors import (
    KeycloakTokenExpiredError,
    KeycloakTokenInvalidError,
)
from dataspace_control_plane_adapters.infrastructure.keycloak.jwks_cache import JwksCache

logger = logging.getLogger(__name__)

_ALGORITHMS = ["RS256"]
"""Supported signing algorithms.  RS256 is the Keycloak default."""


class OidcVerifier:
    """Verifies OIDC access tokens using cached JWKS from Keycloak.

    Uses ``python-jose`` (``jose``) for JWT decoding and RS256 signature
    verification.  python-jose is imported lazily inside ``verify()`` to keep
    module-level import cost low.

    Parameters
    ----------
    settings:
        ``KeycloakSettings`` with ``client_id`` (audience) and ``realm``.
    jwks_cache:
        A ``JwksCache`` instance.  Shared with ``KeycloakAdminClient`` if needed.
    """

    def __init__(self, settings: KeycloakSettings, jwks_cache: JwksCache) -> None:
        self._settings = settings
        self._cache = jwks_cache

    async def verify(self, token: str) -> dict:
        """Verify an OIDC access token and return its decoded claims.

        Parameters
        ----------
        token:
            Raw JWT string (without 'Bearer ' prefix).

        Returns
        -------
        dict
            Decoded JWT payload as a plain dict.  Keys include ``sub``,
            ``email``, ``realm_access``, ``resource_access``, etc.

        Raises
        ------
        KeycloakTokenExpiredError
            If the token's ``exp`` claim has passed.
        KeycloakTokenInvalidError
            If the signature is invalid, the kid is unknown, or the token is
            malformed.
        """
        # Lazy import — jose pulls in cryptography which is heavy.
        from jose import jwt, JWTError, ExpiredSignatureError  # noqa: PLC0415

        keys = await self._cache.get_keys()
        kid = _extract_kid(token)

        # Attempt verification; retry once on unknown kid (key rotation).
        for attempt in range(2):
            if kid and kid not in keys:
                if attempt == 0:
                    logger.info("kid=%r not in JWKS cache; refreshing", kid)
                    await self._cache.refresh()
                    keys = await self._cache.get_keys()
                    continue
                raise KeycloakTokenInvalidError(
                    f"JWT key id {kid!r} not found in Keycloak JWKS after refresh"
                )

            # Build the JWK set list that jose expects.
            jwk_set = {"keys": list(keys.values())}

            try:
                claims: dict = jwt.decode(
                    token,
                    jwk_set,
                    algorithms=_ALGORITHMS,
                    audience=self._settings.client_id,
                    options={"verify_aud": True, "verify_exp": True},
                )
                return claims
            except ExpiredSignatureError as exc:
                raise KeycloakTokenExpiredError(str(exc)) from exc
            except JWTError as exc:
                error_msg = str(exc)
                # If the error is a kid mismatch and we haven't refreshed yet, retry.
                if attempt == 0 and ("kid" in error_msg.lower() or "key" in error_msg.lower()):
                    logger.info("JWT verification failed (attempt 1), refreshing JWKS: %s", exc)
                    await self._cache.refresh()
                    keys = await self._cache.get_keys()
                    continue
                raise KeycloakTokenInvalidError(
                    f"JWT verification failed: {exc}"
                ) from exc

        # Should not reach here, but mypy/type-checkers require a return.
        raise KeycloakTokenInvalidError("Token verification failed after JWKS refresh")


def _extract_kid(token: str) -> str | None:
    """Extract the ``kid`` header from a JWT without verifying the signature.

    Returns ``None`` if the header cannot be parsed (malformed tokens will
    fail at the full decode step anyway).
    """
    try:
        # Lazy import.
        from jose.utils import base64url_decode  # noqa: PLC0415
        import json as _json  # noqa: PLC0415
        import base64  # noqa: PLC0415

        header_b64 = token.split(".")[0]
        # Add padding if needed.
        padded = header_b64 + "=" * (-len(header_b64) % 4)
        header_bytes = base64.urlsafe_b64decode(padded)
        header: dict = _json.loads(header_bytes)
        return header.get("kid")
    except Exception:  # noqa: BLE001
        return None
