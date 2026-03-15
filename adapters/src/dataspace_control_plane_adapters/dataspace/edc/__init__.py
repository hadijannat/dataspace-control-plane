"""Eclipse Dataspace Components (EDC) adapter.

Exposes the EDC Management API as adapter-layer clients and implements
the core/ ports:
- AgreementRegistryPort  (contracts domain)
- CatalogLookupPort      (contracts domain)
- ConnectorProvisioningPort (onboarding domain)

Import from `.api` for the stable public surface.
"""
from __future__ import annotations
