"""
ECOSYSTEM PACK TEMPLATE
=======================
Copy this directory and rename it to your ecosystem name (e.g. ``idsa/``, ``gaia_x_eu/``).

Required files:
  __init__.py       (this file, emptied)
  manifest.toml     (pack declaration — copy manifest.toml.example and fill in)
  api.py            (MANIFEST + PROVIDERS dict exported at module level)
  requirements.py   (RequirementProvider implementation)
  evidence.py       (EvidenceAugmenter implementation)
  vocab/pinned/     (normative assets with provenance — no runtime fetches)
  rules/            (YAML rule catalogs)

Optional files (implement only what your ecosystem needs):
  identifiers.py         (IdentifierSchemeProvider)
  policy_profile/        (PolicyDialectProvider + PurposeCatalogProvider)
  credential_profiles.py (CredentialProfileProvider)
  hooks.py               (ProcedureHookProvider)
  twin_templates.py      (TwinTemplateProvider)
  ui_schema.py           (UiSchemaProvider)

Pack kind conventions:
  pack_kind = "ecosystem"
  activation_scope = "tenant"       (most ecosystems activate per-tenant)
  default_priority = 100            (ecosystem packs lose to regulation and custom)

Dependency direction (read only — never mutate):
  core/    — canonical domain models and invariants
  schemas/ — pinned normative schema artifacts

Forbidden:
  - HTTP clients, DB connections, Temporal SDK, FastAPI
  - Runtime fetching of normative sources (pin under vocab/pinned/ instead)
  - Redefining canonical types from core/
"""

# Step 1: Copy manifest.toml.example → manifest.toml and fill in pack_id, version, etc.
# Step 2: Implement your RequirementProvider in requirements.py
# Step 3: Add your YAML rule catalogs under rules/
# Step 4: Pin normative sources under vocab/pinned/ with provenance metadata in manifest.toml
# Step 5: Export MANIFEST and PROVIDERS from api.py
#         MANIFEST = _minimal_manifest(...) or PackManifest.from_toml(Path(__file__).parent / "manifest.toml")
#         PROVIDERS = {"RequirementProvider": YourRequirementProvider(), ...}
