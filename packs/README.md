# `packs/` — Versioned Rules and Profiles

`packs/` is the repository’s versioned rules-and-profile layer. It sits above
`core/` and `procedures/` as a plugin surface, and below `apps/` as
runtime-loaded configuration and code.

## Runtime Contract

- Each concrete pack exports `MANIFEST` and `PROVIDERS` from `api.py`.
- `PROVIDERS` may register either one provider instance or a list of provider
  instances for a capability. The registry flattens them per pack in
  deterministic order.
- The loader imports built-in packs first, then discovers in-repo custom packs
  from:
  - `src/dataspace_control_plane_packs/custom/examples/*/api.py`
  - `src/dataspace_control_plane_packs/custom/org_packs/*/api.py`
- Resolver order is deterministic: required dependencies first, then
  `default_priority`, then `pack_id`.
- Activation caching is keyed by a fingerprint of
  `scope + requested_packs + pack_options + compatibility_context`.

## Provenance Envelope

Every emitted pack artifact uses the reserved `_pack_provenance` key.

```json
{
  "_pack_provenance": {
    "records": {
      "<pack_id>": {
        "pack_id": "<pack_id>",
        "pack_version": "<version>",
        "rule_ids": ["..."],
        "source_uris": ["..."],
        "source_versions": ["..."],
        "generated_at": "<utc-timestamp>",
        "activation_scope": "<scope>",
        "rule_bundle_hash": "<sha256>"
      }
    }
  }
}
```

Reducers and pack combinators must preserve existing `_pack_provenance.records`
and append new records instead of overwriting earlier ones.

## Source Pinning Rules

- `manifest.toml` is the source of truth for normative assets.
- Every `normative_sources.local_filename` must resolve to a real file under
  `vocab/pinned/` or a `vendor/` subtree inside the owning pack.
- Loader registration fails if a pinned file is missing or if its SHA-256
  checksum does not match the manifest.
- Authored rule YAML under `rules/` is treated as derived pack data, not as the
  upstream normative source.

## Reducer Precedence

- Validation: union warnings and infos; optionally short-circuit on the first
  blocking error.
- Evidence: merge augmenters without dropping previously-added fields.
- Policy compilation: route by dialect.
- Identifier schemes: namespace by `scheme_id`; duplicates are errors.
- Defaults: apply in this order so later wins:
  `shared/base -> ecosystem -> regulation -> custom`.
- Custom overlays may tighten active regulatory rules, but may not weaken them.

## Downstream Follow-up Notes

This PR intentionally stays inside `packs/`. The following consumers need
follow-up work in their own roots:

- `procedures/`: consume pack hook outputs and Catena-X `review_flags`.
- `apps/`: expose activation/profile selection and pack provenance to operators.
- `tests/`: add cross-root compatibility and end-to-end workflow coverage.
- `docs/`: update compliance mappings, architecture docs, and operator guidance.
