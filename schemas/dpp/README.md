# schemas/dpp — Digital Product Passport

Technology-level passport schema layer. Regulation-specific field lists live in `packs/`.

## Structure

| Subdirectory | Contents |
|---|---|
| `source/base/` | Technology-neutral passport envelope, subject, lifecycle, link, access class |
| `source/implementation_profiles/aas_dpp4o/` | AAS DPP4.0 shell/submodel binding, id-link, completeness |
| `source/exports/` | Registry submission and evidence export envelopes |
| `bundles/` | Compound bundle documents |
| `examples/valid/` | Valid passport instances |
| `examples/invalid/` | Instances that must fail |
| `tests/` | Pytest tests |

## Design decisions

- **Technology-neutral base** — `source/base/` has no ESPR delegated-act fields, no battery-specific access audiences, no Catena-X terms.
- **AAS DPP4.0 binding is explicit** — the `aas_dpp4o/` profile constrains how the base passport maps to AAS shells and submodels.
- **Predecessor/successor linkage** — modelled in `passport-link.schema.json` so all regulation packs can reuse it.
- **Lifecycle is separate** — `passport-lifecycle.schema.json` models state transitions; regulation packs add constraints on when transitions are allowed.
- **Registry and evidence export** — `source/exports/` holds the envelope shape for external submissions.

## Upstream standards

- IDTA DPP4.0 — AAS-based, semantically unique, machine-readable, access-controlled
- IDTA AAS Release 25-01 — binding for shell/submodel representation
