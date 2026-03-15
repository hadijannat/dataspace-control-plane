"""Dataspace Protocol (DSP 2025-1) adapter.

This adapter owns:
- DSP 2025-1 message schemas (Pydantic models)
- Inbound message validation
- Canonical mappers (DSP messages → plain dicts)
- Port implementation for AgreementRegistryPort (protocol ACK side)
- TCK integration stubs
- Test fixtures

It does NOT know about EDC management APIs, connector provisioning,
or any vendor-specific transport. Protocol only.

Import from `.api` for the stable public surface.
"""
from __future__ import annotations
