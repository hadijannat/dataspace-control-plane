# Schema Family: `dpp`

> Technology-neutral Digital Product Passport envelope schemas — base passport shape, lifecycle, access classes, predecessor/successor linkage, and AAS DPP4.0 implementation profile bindings.

**Family version:** 1.0.0  
**Validation dialect:** `https://json-schema.org/draft/2020-12/schema`  
**Effective from:** 2026-03-14  

## Upstream Standards

- **IDTA DPP4.0** 4.0  
  https://industrialdigitaltwin.org/dpp4-0
- **IDTA AAS Release 25-01** 25-01  
  https://industrialdigitaltwin.io/aas-specifications/IDTA-01001-3-0

## Local Source Schemas

## Published Bundles

- `bundles/access-class.bundle.schema.json`
- `bundles/completeness.bundle.schema.json`
- `bundles/evidence-envelope.bundle.schema.json`
- `bundles/id-link.bundle.schema.json`
- `bundles/passport-envelope.bundle.schema.json`
- `bundles/passport-lifecycle.bundle.schema.json`
- `bundles/passport-link.bundle.schema.json`
- `bundles/passport-subject.bundle.schema.json`
- `bundles/registry-envelope.bundle.schema.json`
- `bundles/shell-binding.bundle.schema.json`
- `bundles/submodel-binding.bundle.schema.json`

| File | Title | Description |
|------|-------|-------------|
| `source/base/access-class.schema.json` | Passport Access Class | A named access class for a Digital Product Passport. Defines who belongs to this class and which fie |
| `source/base/passport-envelope.schema.json` | Digital Product Passport Envelope | Technology-neutral envelope for a Digital Product Passport. Captures the passport identity, subject  |
| `source/base/passport-lifecycle.schema.json` | Passport Lifecycle State | Current lifecycle state and transition history of a Digital Product Passport. Models the technology- |
| `source/base/passport-link.schema.json` | Passport Link | A typed link between two Digital Product Passports. The base schema models reusable relationship kin |
| `source/base/passport-subject.schema.json` | Passport Subject | The physical or digital product that a Digital Product Passport describes. Captures the unique ident |
| `source/exports/evidence-envelope.schema.json` | DPP Evidence Export Envelope | Envelope for exporting evidence associated with a Digital Product Passport — test reports, declarati |
| `source/exports/registry-envelope.schema.json` | DPP Registry Submission Envelope | Envelope for submitting a Digital Product Passport to an external product registry. Contains passpor |
| `source/implementation_profiles/aas_dpp4o/completeness.schema.json` | DPP4.0 Completeness Check | Result of a completeness check on a DPP AAS shell — verifies that all required submodels and key fie |
| `source/implementation_profiles/aas_dpp4o/id-link.schema.json` | AAS DPP4.0 ID Link | Identification link for DPP4.0 — associates a physical asset identifier (QR code, serial number) wit |
| `source/implementation_profiles/aas_dpp4o/shell-binding.schema.json` | AAS DPP4.0 Shell Binding | Binding contract between a Digital Product Passport and its AAS Shell representation. Specifies how  |
| `source/implementation_profiles/aas_dpp4o/submodel-binding.schema.json` | AAS DPP4.0 Submodel Binding | Binding contract for an individual DPP submodel within the AAS DPP4.0 implementation profile. Valida |

## CI Gates

    python schemas/tools/validate.py --family dpp
    pytest tests/unit -k dpp_schemas
    pytest tests/compatibility -k dpp

---
*Generated 2026-03-15 by `schemas/tools/generate_docs.py`*
