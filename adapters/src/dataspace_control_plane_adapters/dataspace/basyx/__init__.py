"""BaSyx AAS runtime integration adapter.

Provides REST clients for the BaSyx AAS Registry, Submodel Registry, and
Submodel Repository (BaSyx v3 API / AAS Part 2 spec).

Ports implemented:
- AasRegistryPort      (core/domains/twins/ports.py)
- TwinEndpointProbePort (core/domains/twins/ports.py)

AAS IDs are base64URL-encoded as required by AAS Part 2 API specification.
"""
from __future__ import annotations
