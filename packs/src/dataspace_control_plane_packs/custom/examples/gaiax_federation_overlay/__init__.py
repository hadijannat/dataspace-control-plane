"""Reference Gaia-X federation overlay example.

This demonstrates how to create a federation-specific overlay on top of
the base gaia_x pack. A federation may:
  - Select a subset of Gaia-X trust anchors
  - Add federation-specific compliance rules
  - Override the policy dialect with federation extensions

To use as a real federation overlay:
  1. Copy to custom/org_packs/<federation_id>/
  2. Update the FEDERATION_ID and manifest
  3. Register it alongside the base gaia_x pack
"""
