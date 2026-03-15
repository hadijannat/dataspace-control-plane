---
title: "Compliance Mappings"
summary: "Index of compliance obligation narratives, OSCAL component definitions, and evidence matrix for Catena-X, ESPR DPP, and Battery Passport regulatory regimes."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Compliance Mappings

The platform operates under three regulatory regimes simultaneously. This section documents how platform components satisfy the obligations from each regime, in both human-readable narrative form and machine-readable OSCAL format.

## Regulatory Scope

| Regime | Obligation source | Key obligations | Pack |
|--------|-----------------|----------------|------|
| **Catena-X** | Catena-X Operating Model 4.0 + DSP/DCP protocol compliance | DSP catalog endpoint, DCP credential service, ODRL policy evaluation, VC-based member onboarding | `packs/catenax/` |
| **ESPR DPP** | EU Regulation 2024/1781 (ESPR) + delegated acts | DPP creation, accessibility requirements, registry submission, backup copy, data carrier | `packs/espr_dpp/` |
| **Battery Passport** | EU Regulation 2023/1542 (Battery Regulation) + Annex XIII | Annex XIII field tiers (public/authority/legitimate-interest), BattID, state of health, carbon footprint | `packs/battery_passport/` |

## Document Format

Compliance mappings are maintained in two complementary formats:

1. **Narratives** (human-readable): Documents the obligation → platform component → implementation status mapping in plain English. Suitable for regulatory submissions, audit interviews, and operator orientation.
2. **OSCAL** (machine-readable): NIST Open Security Controls Assessment Language 1.1.2 YAML files. Suitable for automated compliance verification, tool integration, and interoperability with GRC platforms.

## Responsibility Matrix

Which platform layer satisfies which obligation class:

| Obligation class | Satisfied by |
|----------------|-------------|
| DSP catalog endpoint (data offer discovery) | `adapters/dataspace/dsp/` + `apps/edc-extension/` |
| DCP credential service (VC presentation acceptance) | `adapters/dataspace/dcp/` |
| ODRL policy evaluation (Catena-X profiles) | `packs/catenax/` + `adapters/dataspace/dsp/` |
| VC issuance and member onboarding | `procedures/trust/` + `adapters/infra/vault/` |
| DPP creation and field completeness | `packs/espr_dpp/` + `packs/battery_passport/` + `schemas/dpp/` |
| DPP registry submission | `procedures/compliance/` + `adapters/dataspace/dpp_registry/` |
| Battery Annex XIII access tiers | `packs/battery_passport/annex_xiii/` + `schemas/dpp/source/base/access-class.schema.json` |
| Evidence emission and signing | `procedures/` (all workflows emitting evidence) + `adapters/infra/vault/` |
| Usage metering | `apps/control-api/` + `adapters/messaging/kafka/` + `schemas/metering/` |
| Audit trail | All evidence-emitting workflows + `core/audit/` + append-only `evidence_records` table |

## Evidence Matrix

See [evidence-matrix/index.md](evidence-matrix/index.md) for the full obligation → evidence artifact → schema → storage mapping.

## OSCAL Files

| File | Type | Content |
|------|------|---------|
| [oscal/profiles/catena-x-profile.yaml](oscal/profiles/catena-x-profile.yaml) | OSCAL Profile | Catena-X participation control selection |
| [oscal/component-definitions/platform-component.yaml](oscal/component-definitions/platform-component.yaml) | OSCAL Component Definition | Platform components and their implemented control requirements |
| [oscal/mappings/battery-passport-mapping.yaml](oscal/mappings/battery-passport-mapping.yaml) | OSCAL Mapping | Battery Regulation Annex XIII → ESPR framework control mapping |

## Compliance Gap Status

| Regime | Implementation status | Blocking gaps |
|--------|----------------------|--------------|
| Catena-X | Partial — DSP/DCP adapters and ODRL pack scaffolded; full protocol surfaces pending apps/ implementation | DSP catalog endpoint not yet implemented; DCP VC presentation endpoint not yet live |
| ESPR DPP | Partial — schema family and pack scaffolded; registry adapter pending | Delegated acts not yet published (Risk R-04); DPP registry adapter not yet implemented |
| Battery Passport | Partial — Annex XIII field tier structure implemented; AAS serialization profile pending | AAS adapter not yet implemented; BattID generation not yet wired to pack |
