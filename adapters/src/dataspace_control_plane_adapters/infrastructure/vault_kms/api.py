"""Public API surface for the vault_kms infrastructure adapter.

Import only from this module when wiring the adapter in apps/ container code.
Internal implementation modules are considered private.

Example:
    from dataspace_control_plane_adapters.infrastructure.vault_kms.api import (
        make_vault_ports,
        VaultSettings,
        VaultTransitSigner,
        VaultPkiIssuer,
        VaultKeyRegistry,
        VaultHealthProbe,
    )
    cfg = VaultSettings()
    ports = make_vault_ports(cfg)
"""
from __future__ import annotations

from .config import VaultSettings
from .errors import (
    VaultError,
    VaultSealedError,
    VaultKeyNotFoundError,
    VaultAuthError,
    VaultTransitError,
    VaultPkiError,
)
from .health import VaultHealthProbe
from .key_registry import VaultKeyRegistry
from .pki_issuer import VaultPkiIssuer
from .ports_impl import VaultSignerPortImpl, make_vault_ports
from .transit_signer import VaultTransitSigner
from .transit_verifier import VaultTransitVerifier
from .transit_hmac import VaultTransitHmac
from .certificate_lifecycle import CertificateLifecycleManager

__all__ = [
    # Configuration
    "VaultSettings",
    # Errors
    "VaultError",
    "VaultSealedError",
    "VaultKeyNotFoundError",
    "VaultAuthError",
    "VaultTransitError",
    "VaultPkiError",
    # Concrete adapters
    "VaultTransitSigner",
    "VaultTransitVerifier",
    "VaultTransitHmac",
    "VaultPkiIssuer",
    "VaultKeyRegistry",
    "CertificateLifecycleManager",
    # Port implementations
    "VaultSignerPortImpl",
    # Health
    "VaultHealthProbe",
    # Factory
    "make_vault_ports",
]
