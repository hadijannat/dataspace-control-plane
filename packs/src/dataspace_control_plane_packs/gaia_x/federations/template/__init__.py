"""Template for a Gaia-X federation overlay pack.

Copy this directory and rename it to the federation ID (e.g. ``eu_cloud/``, ``catena_x_gx/``).

Required attributes to implement:
  FEDERATION_ID: str          — unique federation identifier
  EFFECTIVE_FROM: str         — ISO 8601 date when federation rules take effect
  TRUST_ANCHOR_SUBSET: list   — list of DID strings from the Gaia-X trust anchor registry
  ADDITIONAL_RULES: list      — additional RuleDefinition instances beyond the baseline

Optional overrides:
  - TrustAnchorOverlayProvider: filter/augment the base anchor set
  - PolicyDialectProvider: extend the ODRL dialect for federation terms
  - RequirementProvider: add federation-specific compliance rules

Registration:
  Add the federation overlay to packs/loader.py BUILTIN_PACKS or register
  via Python entry-points for external federation packages.
"""

FEDERATION_ID = "template"
EFFECTIVE_FROM = "2026-01-01"
TRUST_ANCHOR_SUBSET: list = []
ADDITIONAL_RULES: list = []
