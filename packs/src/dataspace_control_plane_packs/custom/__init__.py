"""Custom pack namespace — developer scaffolds, reference examples, and organization-specific overlays.

This namespace is NOT a runtime pack itself. It provides:
  - templates/ : developer scaffolds for new packs
  - examples/  : tested, runnable reference packs
  - org_packs/ : actual in-repo custom packs (organization-specific)

Custom packs may:
  - Add stricter internal controls (but NEVER weaken regulatory requirements)
  - Add enterprise-specific evidence fields
  - Add federation-specific Gaia-X overlays
  - Add organization-specific UI metadata

Custom packs may NOT:
  - Weaken active legal requirements
  - Replace canonical policy semantics
  - Bypass active ecosystem trust requirements
"""
