---
title: "Battery Passport Compliance Narrative"
summary: "How the platform satisfies EU Regulation 2023/1542 (Battery Regulation) obligations for Battery Passport creation, Annex XIII field tiers, and AAS serialization."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

## Obligation Source

- **EU Regulation 2023/1542** — Battery Regulation, repealing Directive 2006/66/EC
- **Annex XIII** — Defines the mandatory field list for the Battery Passport, organized into three access tiers: public, authority, and legitimate-interest
- **Commission Delegated Regulation (EU) 2024/1328** — Specifies the detailed data attributes for Annex XIII (published April 2024)
- **IDTA AAS Release 25-01 + Battery Passport submodel template** — Digital twin serialization standard for Battery Passports

## Key Obligations

### BP-01: Battery Identifier (BattID)

Each battery subject to the regulation must have a unique Battery Identifier (BattID) that:

- Is globally unique
- Links to the Battery Passport
- Is physically inscribed or attached to the battery
- Follows the format specified in the delegated regulation

**Platform component**: `packs/battery_passport/battid/` implements BattID generation (format: `BATT-{YYYY}{MM}{DD}-{manufacturer_code}-{serial}`). The BattID is set during passport creation and is immutable thereafter.

**Status**: BattID format defined. Generation implementation pending (Wave 2).

**Schema reference**: `schemas/dpp/source/base/passport-base.schema.json` — `batteryIdentifier` field.

### BP-02: Annex XIII Field Tiers

Annex XIII defines three access tiers for Battery Passport data:

| Tier | Accessible to | Examples |
|------|--------------|---------|
| **Public** | Any person via the data carrier | Battery model, chemistry, rated capacity, carbon footprint per kWh |
| **Authority** | Customs, market surveillance, law enforcement | Cell chemical composition, hazardous substances, compliance documentation |
| **Legitimate interest** | Economic operators, repair/recycling companies | Detailed material composition, state of health data, battery management system data |

**Platform component**: `packs/battery_passport/annex_xiii/` defines the field list for each access tier. `schemas/dpp/source/base/access-class.schema.json` defines the `readablePaths` format that specifies which JSON paths are accessible per tier.

**Status**: Access tier structure fully implemented. Field list coverage for all three tiers is complete for Annex XIII as specified in Delegated Regulation 2024/1328.

### BP-03: State of Health Data

The Battery Passport must include state of health (SoH) data when the battery is in secondary use (e.g., repurposed from EV to stationary storage). SoH data includes capacity fade, internal resistance, and the number of charge/discharge cycles.

**Platform component**: SoH fields are defined in `packs/battery_passport/annex_xiii/` under the legitimate-interest tier. The `BatteryPassportPack.apply()` method validates SoH field completeness when `secondary_use_flag: true` is set.

**Status**: Field definitions complete. Validation logic partially implemented.

### BP-04: Carbon Footprint

The Battery Passport must include the carbon footprint value (kgCO2e/kWh) calculated per the methodology specified in the regulation. The carbon footprint must be updated when significant changes occur.

**Platform component**: `carbonFootprint` is a required public-tier field in `packs/battery_passport/annex_xiii/public_tier.py`. The pack validator rejects a passport that is missing this field or has a non-numeric value.

**Status**: Validation implemented. See `tests/unit/packs/validators/test_battery_passport_validators.py`.

### BP-05: AAS Serialization

The Battery Passport must be serializable as an IDTA Asset Administration Shell shell descriptor + submodels for interoperability with industrial digital twin infrastructure. The BaSyx AAS Server stores the shell descriptor.

**Platform component**: `adapters/aas/basyx/` implements the BaSyx AAS Part 2 REST client. `packs/battery_passport/aas_profile/` defines the AAS implementation profile mapping Battery Passport fields to AAS submodel templates.

**Status**: AAS adapter scaffolded. AAS implementation profile structure defined. Submodel serialization pending (Wave 2).

**Schema reference**: `schemas/aas/source/` — AAS Release 25-01 schemas.

## Annex XIII Coverage Map

| Field | Tier | Schema path | Pack validator |
|-------|------|-------------|---------------|
| Battery model | Public | `fields.batteryModel` | Required, non-empty string |
| Battery chemistry | Public | `fields.batteryChemistry` | Required, enum from IDTA chemistry list |
| Rated capacity (kWh) | Public | `fields.ratedCapacity.value` | Required, positive number |
| Carbon footprint (kgCO2e/kWh) | Public | `fields.carbonFootprint.value` | Required, positive number |
| Hazardous substances | Authority | `fields.hazardousSubstances` | Required array (authority tier only) |
| Cell chemical composition | Authority | `fields.cellComposition` | Required when chemistry = LFP or NMC |
| State of health | Legitimate interest | `fields.stateOfHealth.capacityFadePercent` | Required when `secondaryUse: true` |
| Internal resistance | Legitimate interest | `fields.stateOfHealth.internalResistanceMOhm` | Required when `secondaryUse: true` |

## Regulatory Timeline

| Date | Milestone |
|------|-----------|
| 2023-08-17 | EU Regulation 2023/1542 entered into force |
| 2024-02-18 | Mandatory for large industrial batteries (> 2 kWh) placed on EU market |
| 2024-04 | Commission Delegated Regulation 2024/1328 published (Annex XIII field details) |
| 2027-02 | Mandatory for LMT (light means of transport) batteries |
| 2028-02 | Mandatory for all EV batteries |

## Schema References

| Schema file | Use |
|------------|-----|
| `schemas/dpp/source/base/passport-base.schema.json` | Battery Passport base structure |
| `schemas/dpp/source/base/access-class.schema.json` | Annex XIII access tier field path definitions |
| `schemas/aas/source/` | AAS Release 25-01 shell and submodel schemas |
| `schemas/dpp/source/exports/evidence-envelope.schema.json` | Evidence artifact for Battery Passport creation events |

## Related OSCAL Artifacts

- [Battery Passport profile](../oscal/profiles/battery-passport-profile.yaml)
- [Battery Passport mapping](../oscal/mappings/battery-passport-mapping.yaml)
- [Platform component definition](../oscal/component-definitions/platform-component.yaml)
