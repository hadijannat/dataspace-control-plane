# Schema Family: `aas`

> AAS implementation profile schemas for shell, submodel, descriptor, security, and value-only payloads — derived from IDTA Release 25-01.

**Family version:** 1.0.0  
**Validation dialect:** `https://json-schema.org/draft/2020-12/schema`  
**Effective from:** 2026-03-14  

## Upstream Standards

- **IDTA AAS Part 1 Metamodel** 25-01  
  https://industrialdigitaltwin.io/aas-specifications/IDTA-01001-3-0
- **IDTA AAS Part 2 APIs** 25-01  
  https://industrialdigitaltwin.io/aas-specifications/IDTA-01002-3-0
- **IDTA AAS Part 4 Security** 25-01  
  https://industrialdigitaltwin.io/aas-specifications/IDTA-01004-1-0
- **admin-shell-io AAS Schemas** 3.1.0  
  https://github.com/admin-shell-io/aas-specs/tree/v3.1.0/schemas

## Local Source Schemas

## Published Bundles

- `bundles/aasx-manifest.bundle.schema.json`
- `bundles/access-rule.bundle.schema.json`
- `bundles/access-token-claims.bundle.schema.json`
- `bundles/endpoint-ref.bundle.schema.json`
- `bundles/object-attributes.bundle.schema.json`
- `bundles/shell-descriptor.bundle.schema.json`
- `bundles/shell.bundle.schema.json`
- `bundles/subject-attributes.bundle.schema.json`
- `bundles/submodel-descriptor.bundle.schema.json`
- `bundles/submodel.bundle.schema.json`
- `bundles/value-only.bundle.schema.json`

| File | Title | Description |
|------|-------|-------------|
| `source/profiles/aasx-manifest.schema.json` | AASX Package Manifest Reference | Reference-level schema for an AASX package manifest entry. An AASX file is a ZIP archive (OPC/ECMA-3 |
| `source/profiles/endpoint-ref.schema.json` | AAS Endpoint Reference | Protocol-specific endpoint descriptor for an AAS Shell or Submodel. Captures interface name, protoco |
| `source/profiles/shell-descriptor.schema.json` | AAS Shell Descriptor | AAS Shell Descriptor shape per IDTA Release 25-01 Part 2 APIs. Used by the AAS Registry to describe  |
| `source/profiles/shell.schema.json` | AAS Shell Instance | Implementation profile for an AAS Asset Administration Shell (shell instance) per IDTA Release 25-01 |
| `source/profiles/submodel-descriptor.schema.json` | AAS Submodel Descriptor | AAS Submodel Descriptor per IDTA Release 25-01 Part 2. Registered in the AAS Registry; describes whe |
| `source/profiles/submodel.schema.json` | AAS Submodel Instance | Implementation profile for an AAS Submodel instance per IDTA Release 25-01. Validates the submodel e |
| `source/profiles/value-only.schema.json` | AAS Value-Only Payload | Map of idShort → value for each submodel element. Nested SubmodelElementCollections are represented  |
| `source/security/access-rule.schema.json` | AAS Access Rule | AAS Part 4 ABAC access rule. Rules can target registries, repositories, full submodels, or individua |
| `source/security/access-token-claims.schema.json` | AAS Access Token Claims | Claims expected in an OAuth2/JWT access token presented to an AAS API endpoint. Validates the shape  |
| `source/security/object-attributes.schema.json` | AAS Object Attributes | ABAC object attributes for AAS Part 4. Describes what resource is being accessed. Can target a regis |
| `source/security/subject-attributes.schema.json` | AAS Subject Attributes | ABAC subject attributes for AAS Part 4. Describes who is requesting access: role class, optional BPN |

## CI Gates

    python schemas/tools/validate.py --family aas
    python schemas/tools/pin_upstream.py --dry-run --family aas
    pytest tests/unit -k aas_schemas
    pytest tests/compatibility -k aas

---
*Generated 2026-03-15 by `schemas/tools/generate_docs.py`*
