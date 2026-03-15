"""Top-level import surface for the adapters package.

Each sub-group exposes its own api.py. This module re-exports the
adapter-factory functions used by apps/temporal-workers and apps/control-api
at container startup.

Usage pattern:
    from dataspace_control_plane_adapters.api import build_postgres_ports, build_edc_ports, ...
    ports = build_postgres_ports(cfg)

All concrete adapter wiring happens inside container/entrypoint code (apps/).
Never import adapters from core/ or procedures/.
"""
from __future__ import annotations

# Lazy re-exports so the top-level import is cheap and does not pull in
# heavy SDK dependencies (Temporal, Vault, OTel, etc.) unless explicitly used.

__all__: list[str] = []
