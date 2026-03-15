# Schema Family: `vc`

> Verifiable Credential and Presentation envelope schemas, pinned W3C contexts, integrity proof metadata, and status references.

**Family version:** 1.0.0  
**Validation dialect:** `https://json-schema.org/draft/2020-12/schema`  
**Effective from:** 2026-03-14  

## Upstream Standards

- **W3C Verifiable Credentials Data Model 2.0** 2.0  
  https://www.w3.org/TR/vc-data-model-2.0/
- **W3C Data Integrity 1.0** 1.0  
  https://www.w3.org/TR/vc-data-integrity/
- **W3C Bitstring Status List v1.0** 1.0  
  https://www.w3.org/TR/vc-bitstring-status-list/
- **W3C Controlled Identifiers** 1.0  
  https://www.w3.org/TR/cid-1.0/

## Local Source Schemas

## Published Bundles

- `bundles/bitstring-status-ref.bundle.schema.json`
- `bundles/credential-envelope.bundle.schema.json`
- `bundles/credential-schema-ref.bundle.schema.json`
- `bundles/presentation-envelope.bundle.schema.json`
- `bundles/profile-base.bundle.schema.json`
- `bundles/proof-metadata.bundle.schema.json`
- `bundles/status-ref.bundle.schema.json`

| File | Title | Description |
|------|-------|-------------|
| `source/envelope/credential-envelope.schema.json` | Verifiable Credential Envelope | Structural shape of a W3C Verifiable Credential (VC Data Model 2.0). Validates the outer envelope —  |
| `source/envelope/credential-schema-ref.schema.json` | Credential Schema Reference | Reference to the schema that describes the credential subject fields. Appears inside credentialSchem |
| `source/envelope/presentation-envelope.schema.json` | Verifiable Presentation Envelope | Structural shape of a W3C Verifiable Presentation (VC Data Model 2.0). Wraps one or more Verifiable  |
| `source/integrity/proof-metadata.schema.json` | Proof Metadata | Structure of a cryptographic proof attached to a Verifiable Credential or Presentation. Validates th |
| `source/integrity/status-ref.schema.json` | Credential Status Reference | Reference to a credential status mechanism within a Verifiable Credential. Validates the outer statu |
| `source/profiles/profile-base.schema.json` | VC Profile Base | Abstract base for platform-specific credential profile schemas. Each concrete credential type (e.g.  |
| `source/status/bitstring-status-ref.schema.json` | Bitstring Status List Entry Reference | Validates a BitstringStatusListEntry status reference. Identifies the position of this credential in |

## CI Gates

    python schemas/tools/validate.py --family vc
    python schemas/tools/pin_upstream.py --dry-run --family vc
    pytest tests/unit -k vc_schemas
    pytest tests/compatibility -k vc

---
*Generated 2026-03-15 by `schemas/tools/generate_docs.py`*
