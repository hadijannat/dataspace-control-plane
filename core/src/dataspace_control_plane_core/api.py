"""
Public API surface for dataspace-control-plane-core.
Import from here or from individual sub-package api.py files.
Do not import from model/, services.py, or other internals.
"""
# Sub-package APIs are imported lazily to avoid circular imports.
# Example consumer:
#   from dataspace_control_plane_core.domains.tenant_topology.api import TenantTopologyService
#   from dataspace_control_plane_core.canonical_models.identity import DidUri
