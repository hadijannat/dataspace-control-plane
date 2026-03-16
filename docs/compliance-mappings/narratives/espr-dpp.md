---
title: "ESPR Digital Product Passport Compliance Narrative"
summary: "How the platform satisfies EU Regulation 2024/1781 (ESPR) obligations for Digital Product Passport creation, registry submission, and accessibility."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

## Obligation Source

- **EU Regulation 2024/1781 (ESPR)** — Ecodesign for Sustainable Products Regulation, mandating Digital Product Passports for regulated product categories
- **Delegated acts (pending)** — Category-specific field requirements published separately per product category; most are not yet published as of 2026-03-14
- **DPP Access Rights Regulation** — defines which actors can access which tiers of DPP data

## Key Obligations

### ESPR-01: DPP Creation for Regulated Product Categories

Economic operators must create a Digital Product Passport for each product unit (or product model, depending on category) when placing it on the EU market. The DPP must include: product identifier, manufacturer information, material composition, environmental performance data, and end-of-life instructions.

**Platform component**: `packs/espr_dpp/` implements the field completeness validator and field enrichment rules. `schemas/dpp/source/` defines the DPP 4.0 data shape. `procedures/compliance/` implements the `DPPExportWorkflow` that creates and registers DPPs.

**Status**: Pack scaffolded with field structure and validator skeleton. DPP 4.0 schema family implemented. Workflow integration pending (Wave 2). **Gap**: Specific field requirements depend on delegated acts that have not yet been published for most product categories.

### ESPR-02: Registry Submission and Accessibility

DPPs must be submitted to the EU-operated DPP registry and be accessible to operators (full data), customs authorities (authority-tier data), and consumers (public-tier data) via a data carrier (e.g., QR code) or digital link.

**Platform component**: `adapters/dataspace/dpp_registry/` implements the registry submission client. `procedures/compliance/DPPExportWorkflow` orchestrates the submission. `packs/espr_dpp/access_tiers/` defines the data access tier logic.

**Status**: Registry adapter scaffolded. Access tier structure defined. Workflow pending (Wave 2).

### ESPR-03: Backup Copy

A backup copy of the DPP must be maintained by the economic operator independently of the EU registry. The backup must be accessible even if the registry is unavailable.

**Platform component**: The DPP record is stored in Postgres (append-only status history) and the AAS shell is stored in BaSyx. Both provide independent backup storage. Evidence envelopes in Postgres contain the full DPP payload hash.

**Status**: Storage architecture defined. BaSyx AAS adapter pending (Wave 2).

### ESPR-04: Data Carrier

Each physical product unit must bear a data carrier (QR code, NFC tag, or digital link) pointing to the DPP. The platform generates the data carrier URL at DPP publication time.

**Platform component**: The `DPPExportWorkflow` generates the data carrier URL (format: `https://dpp.your-org.internal/passports/{passportId}`) after successful registry submission and includes it in the publication response.

**Status**: URL generation logic defined in `packs/espr_dpp/`. Integration pending (Wave 2).

## Gap Status

!!! warning "Delegated Acts Not Yet Published"
    The most significant compliance gap for ESPR is that the delegated acts defining
    product-category-specific field requirements have not yet been published by the
    European Commission for most categories. `packs/espr_dpp/delegated_acts/`
    contains a template structure for delegated act field definitions. This template
    **must be updated** when the relevant delegated acts are published. See
    **Risk R-04** in `docs/arc42/11-risks-and-technical-debt.md` for tracking.

| Obligation | Status | Gap |
|-----------|--------|-----|
| ESPR-01: DPP creation | Partial | Delegated acts pending; field lists are templates |
| ESPR-02: Registry submission | Scaffolded | Registry adapter implementation pending |
| ESPR-02: Accessibility tiers | Partial | Access tier logic defined; enforcement pending |
| ESPR-03: Backup copy | Architecture defined | BaSyx AAS adapter pending |
| ESPR-04: Data carrier generation | Partial | URL generation defined; QR code generation pending |

## Schema References

| Schema file | Use |
|------------|-----|
| `schemas/dpp/source/base/passport-base.schema.json` | DPP 4.0 base structure |
| `schemas/dpp/source/base/access-class.schema.json` | Access tier definitions (public, authority, legitimate-interest) |
| `schemas/dpp/source/exports/evidence-envelope.schema.json` | Evidence artifact for DPP creation events |
| `schemas/dpp/source/exports/registry-envelope.schema.json` | Registry submission format |

## Regulatory Timeline

| Date | Milestone |
|------|-----------|
| 2024-08-18 | EU Regulation 2024/1781 entered into force |
| 2025-2026 | Delegated acts published per product category (rolling) |
| 2027+ | DPP mandatory for first product categories (batteries: 2024 for large industrial; other categories per delegated act timeline) |

## Related OSCAL Artifacts

- [Platform component definition](../oscal/component-definitions/platform-component.yaml)
- [Battery Passport mapping](../oscal/mappings/battery-passport-mapping.yaml)
