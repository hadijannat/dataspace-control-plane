# schemas/odrl — ODRL Base Policy Schemas

Base ODRL policy schema family. Policy-profile vocabularies (`cx-policy:*`, Gaia-X) live in `packs/`.

## What is here

| Subdirectory | Contents |
|---|---|
| `vendor/w3c/` | Pinned W3C ODRL JSON-LD context and Turtle vocabulary |
| `vendor/profiles/` | Pinned ecosystem profile artifacts (Catena-X, Gaia-X) |
| `source/base/` | JSON Schema for ODRL offer, agreement, set, permission, prohibition, obligation, constraint, duty |
| `source/ast/` | Internal compact AST and parse-report schemas for non-graph runtime use |
| `derived/jsonld/` | JSON-LD normalized policy forms (generated) |
| `derived/json-schema/` | Normalized JSON Schema artifacts from upstream (generated) |
| `bundles/` | Compound bundle documents |
| `examples/valid/` | Valid ODRL instances |
| `examples/invalid/` | Instances that must fail |
| `tests/` | Pytest tests for this family |

## Design decisions

- **Base here, profiles in packs**: `cx-policy:*` and Gaia-X-specific terms do not belong in base ODRL schemas.
- **Two surfaces**: JSON Schema for structural validation + compact AST for non-graph consumers. Do not require RDF/Turtle parsing for a simple policy check.
- **JSON Schema is structural only**: semantic evaluation (is this purpose allowed?) belongs in `core/` and `packs/`.
- **No vendor lock**: base schemas are W3C-neutral. Profiles are declared as extensions.

## Upstream standards pinned

- W3C ODRL Information Model 2.2 — `vendor/w3c/odrl-context.jsonld`
- W3C ODRL Vocabulary 2.2 — `vendor/w3c/odrl-vocab.ttl`
- Catena-X ODRL Profile 24.05 — `vendor/profiles/catenax-odrl-profile-24.05.jsonld`

## Refreshing vendor artifacts

```bash
python schemas/tools/pin_upstream.py --family odrl
```
