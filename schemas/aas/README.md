# schemas/aas — AAS Serialization and Profile Registry

Implementation profile schemas for AAS Release 25-01 artifacts.

## Structure

| Subdirectory | Contents |
|---|---|
| `vendor/idta-release-25-01/` | Pinned IDTA normative PDF/YAML specs |
| `vendor/admin-shell-io/` | Pinned machine-usable JSON/XML/RDF schemas from admin-shell-io |
| `source/profiles/` | Local implementation profiles: shell, submodel, descriptors, value-only, AASX manifest |
| `source/security/` | AAS Part 4 ABAC: access rules, subject/object attributes, token claims |
| `derived/` | Generated normalized artifacts |
| `bundles/` | Compound bundle documents |
| `examples/valid/` | Valid AAS instances |
| `examples/invalid/` | Instances that must fail validation |
| `tests/` | Pytest tests for this family |

## Design decisions

- **Split by artifact class** — no monolithic `aas.schema.json`. Shell ≠ Submodel ≠ Descriptor ≠ Security.
- **Implementation profiles, not semantics** — `source/profiles/` constrains the shape we accept/emit; it doesn't rewrite AAS Part 1 semantics.
- **Security is separate** — AAS Part 4 ABAC schemas live in `source/security/`, not mixed into profile schemas.
- **Vendor assets are immutable** — only `pin_upstream.py` writes to `vendor/`. PDF docs are for reference; machine-usable schemas are from `admin-shell-io`.
- **No pack semantics here** — Catena-X DPP purpose codes, ESPR delegated act fields, battery-specific access audiences all belong in `packs/`.

## Upstream releases

- IDTA AAS Release 25-01 (Part 1 Metamodel, Part 2 APIs, Part 4 Security)
- admin-shell-io `aas-specs-antora` v25-01 (JSON Schema, XSD, RDF)

## Refreshing vendor artifacts

```bash
python schemas/tools/pin_upstream.py --family aas
```

## Validation

```bash
python schemas/tools/validate.py --family aas
pytest schemas/aas/tests/ -v
```
