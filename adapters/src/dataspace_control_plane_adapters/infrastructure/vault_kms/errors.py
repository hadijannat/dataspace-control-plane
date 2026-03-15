"""Vault KMS adapter-specific error hierarchy.

Rules:
- VaultError is the root of all Vault-layer exceptions.
- All callers translate these into core-layer errors at the service boundary.
- Never include secret material, tokens, or key content in error messages.
"""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.errors import (
    AdapterError,
    AdapterNotFoundError,
    AdapterUnavailableError,
)


class VaultError(AdapterError):
    """Root for all Vault KMS adapter errors."""


class VaultUnavailableError(VaultError, AdapterUnavailableError):
    """Raised when the Vault server is unreachable or returns 5xx responses."""


class VaultSealedError(VaultUnavailableError):
    """Raised when Vault returns a sealed status (HTTP 503 from /sys/health).

    Vault is temporarily unable to serve requests. The operator must unseal.
    """

    def __init__(self) -> None:
        super().__init__(
            "Vault is sealed and cannot serve requests. Operator intervention required.",
            upstream_code=503,
        )


class VaultKeyNotFoundError(AdapterNotFoundError):
    """Raised when the requested Transit or PKI key does not exist in Vault.

    Subclasses AdapterNotFoundError so callers can catch the shared base type.
    """

    def __init__(self, key_id: str, mount: str) -> None:
        super().__init__(
            f"Vault key {key_id!r} not found in mount {mount!r}.",
            upstream_code=404,
        )
        self.key_id = key_id
        self.mount = mount


class VaultAuthError(VaultError):
    """Raised when the Vault token or AppRole credentials are invalid or expired."""

    def __init__(self, message: str = "Vault authentication failed.") -> None:
        super().__init__(message, upstream_code=403)


class VaultTransitError(VaultError):
    """Raised for Transit engine operation failures (sign, verify, hmac)."""


class VaultPkiError(VaultError):
    """Raised for PKI engine operation failures (issue, revoke, tidy)."""
