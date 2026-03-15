"""Namespace for Gaia-X federation-specific overlay packs.

Each federation adds a subpackage here. A federation overlay may:
  - Select a subset of Gaia-X trust anchors
  - Add stricter compliance rules beyond the baseline
  - Define federation-specific credential profiles
  - Override the policy dialect with federation extensions

A federation overlay must NOT:
  - Weaken baseline Gaia-X compliance rules
  - Replace canonical policy semantics
  - Define itself as the universal Gaia-X rule set

See custom/examples/gaiax_federation_overlay/ for a reference implementation.
"""
