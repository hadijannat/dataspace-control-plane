"""Vault KMS port implementations.

Wires the concrete Vault adapters to the core machine_trust port interfaces.
This module is the authoritative wiring point; apps/temporal-workers call
make_vault_ports() during container startup.

Only this module should be imported by apps/ — internal modules (transit_signer,
pki_issuer, etc.) are considered implementation details.
"""
from __future__ import annotations

from .config import VaultSettings
from .transit_signer import VaultTransitSigner


class VaultSignerPortImpl:
    """Delegates SignerPort to VaultTransitSigner.

    # implements core/domains/machine_trust/ports.py SignerPort

    Wraps VaultTransitSigner to fulfil the SignerPort protocol. Keeps the
    port-facing class name stable even if the underlying implementation changes.
    """

    def __init__(self, cfg: VaultSettings) -> None:
        self._signer = VaultTransitSigner(cfg)

    async def sign(self, payload: bytes, key_id: str) -> bytes:
        """Sign *payload* using Vault Transit key *key_id*.

        Args:
            payload: Raw bytes to sign.
            key_id:  Logical or Vault-path key identifier.

        Returns:
            Signature bytes from Vault Transit.
        """
        return await self._signer.sign(payload, key_id)


def make_vault_ports(cfg: VaultSettings) -> dict[str, object]:
    """Construct all Vault-backed port implementations from *cfg*.

    Returns a dict keyed by port role. Callers extract specific ports:
        ports = make_vault_ports(cfg)
        signer = ports["signer"]

    Ports returned:
        "signer"      — VaultSignerPortImpl (implements SignerPort)
        "pki_issuer"  — VaultPkiIssuer (certificate lifecycle helper)
        "key_registry"— VaultKeyRegistry (logical-to-Vault name mapping)
        "health"      — VaultHealthProbe (liveness/readiness probe)
    """
    # Deferred imports keep heavy SDK loads out of module-level evaluation.
    from .pki_issuer import VaultPkiIssuer
    from .key_registry import VaultKeyRegistry
    from .health import VaultHealthProbe

    return {
        "signer": VaultSignerPortImpl(cfg),
        "pki_issuer": VaultPkiIssuer(cfg),
        "key_registry": VaultKeyRegistry(transit_mount=cfg.transit_mount),
        "health": VaultHealthProbe(cfg),
    }
