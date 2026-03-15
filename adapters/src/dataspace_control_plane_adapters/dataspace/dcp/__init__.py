"""DCP (Dataspace Credential Protocol 1.0) adapter.

Implements the DCP credential service, issuer, and verifier surfaces.
All signing operations delegate to infrastructure/vault_kms/ via SignerPort.
No raw private key material is handled here.

Ports implemented:
- CredentialIssuerPort  (core/domains/machine_trust/ports.py)
- PresentationVerifierPort (core/domains/machine_trust/ports.py)
- TrustAnchorResolverPort (core/domains/machine_trust/ports.py)
"""
from __future__ import annotations
