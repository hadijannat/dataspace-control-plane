---
title: "JSON Schema 2020-12 as the house validation dialect for all local schemas"
status: accepted
date: 2026-03-14
decision-makers:
  - schemas-lead
consulted:
  - adapters-lead
  - packs-lead
  - core-lead
  - all-leads
informed:
  - all-leads
---

# JSON Schema 2020-12 as the house validation dialect for all local schemas

## Context and Problem Statement

The `schemas/` layer defines six schema families covering W3C VCs, ODRL policies, IDTA AAS shells, Digital Product Passports, metering events, and enterprise field mappings. These schemas are consumed by: Python validation code in adapters and packs, Redocly for API contract validation, NIST OSCAL validators for compliance artifacts, and CI-level schema diff tooling.

The platform deals with upstream schemas from multiple standards bodies that use different JSON Schema dialects: W3C VC 2.0 references Draft-07, AAS submodel templates reference Draft-07 or older, ODRL 2.2 was specified before JSON Schema existed (it uses JSON-LD). Without a declared house dialect, local schemas would inherit the dialect of the upstream standard they reference, leading to mixed validator behavior.

A single dialect for all local schemas enables uniform tooling: one validator library, one meta-schema reference, one `$ref` resolution model. Vendor-pinned upstream artifacts are exempt from the house dialect requirement but must include provenance metadata.

## Decision Drivers

* Uniform `$id` and `$ref` resolution: all local schemas must use the same `$ref` resolution model to enable cross-family references without ambiguity
* Python toolchain compatibility: the `jsonschema` library (Python 3.12) must fully support the chosen dialect
* Redocly compatibility: Redocly CLI must be able to lint and bundle schemas using the chosen dialect
* Future-proofing: the chosen dialect should be the current IETF standard, not a draft that may diverge
* Breaking-change detection: `diff_schema.py` must support the chosen dialect for compatible/breaking classification
* Consistent meta-schema `$schema` declaration in all local schema files

## Considered Options

* JSON Schema 2020-12 (chosen)
* JSON Schema Draft-07
* OpenAPI 3.1 Schema Object
* TypeSchema

## Decision Outcome

**Chosen option: "JSON Schema 2020-12"**, because it is the current IETF standard (RFC 8259 + draft-bhutton-json-schema-01), has full support in `jsonschema` 4.x+ for Python 3.12, is supported by Redocly CLI 2.x+ for OpenAPI linting, provides the `unevaluatedProperties` and `$dynamicRef` features needed for strict schema composition, and uses a well-defined `$id`/`$ref` resolution model based on URI-reference resolution. Vendor-pinned upstream artifacts (AAS submodel templates, W3C VC context files) are exempt from this requirement and stored in `schemas/*/vendor/` with `provenance.json`.

### Positive Consequences

* Uniform meta-schema declaration: every local schema begins with `"$schema": "https://json-schema.org/draft/2020-12/schema"`
* Consistent `$ref` resolution: all local cross-family references use relative URI paths that resolve unambiguously
* `unevaluatedProperties: false` enables strict schema composition without Draft-07's `additionalProperties` pitfalls when using `allOf`
* `$dynamicRef` enables recursive schema structures (e.g., AAS submodel nesting) without circular reference issues
* `jsonschema` 4.x `Draft202012Validator` provides the reference Python implementation

### Negative Consequences

* Upstream artifacts that use Draft-07 must be stored as vendor-pinned files, not referenced directly by local schemas — this requires transformation or wrapping when local schemas extend upstream types
* Some Redocly features designed for OpenAPI 3.1 Schema Objects (which are a subset of 2020-12) may behave differently when applied to pure JSON Schema 2020-12 files
* `jsonschema` 4.x 2020-12 support requires explicit opt-in (`Draft202012Validator`) — using the default validator will fall back to Draft-07

### Confirmation

`tests/compatibility/test_schema_meta_compliance.py` must verify that all JSON Schema files in `schemas/*/source/` declare `"$schema": "https://json-schema.org/draft/2020-12/schema"`. The test must fail if any local schema uses a different `$schema` value. Vendor files in `schemas/*/vendor/` are excluded from this check.

## Pros and Cons of the Options

### JSON Schema 2020-12

The current IETF JSON Schema standard with `$dynamicRef`, `unevaluatedProperties`, and URI-reference-based `$id`/`$ref` resolution.

* Good, because current IETF standard — no future dialect migration expected
* Good, because `jsonschema` 4.x full support for Python 3.12
* Good, because `unevaluatedProperties` solves `additionalProperties` + `allOf` composition problems
* Good, because Redocly 2.x supports 2020-12 for linting
* Bad, because upstream standards (AAS, W3C VC) reference Draft-07 — vendor wrapping required

### JSON Schema Draft-07

The previous major JSON Schema draft, widely supported by older tooling.

* Good, because widest tooling support — almost every JSON Schema library supports Draft-07
* Good, because W3C VC 2.0 and many AAS artifacts already use Draft-07 — no wrapping needed
* Bad, because `additionalProperties` + `allOf` composition is subtly broken (properties from `allOf` branches are not recognized by `additionalProperties: false`)
* Bad, because no `$dynamicRef` — recursive schemas require `$recursiveRef` (Draft 2019-09) or workarounds
* Bad, because Draft-07 is not an IETF standard and will not receive further updates

### OpenAPI 3.1 Schema Object

A subset of JSON Schema 2020-12 with OpenAPI extensions (`discriminator`, `xml`, `example`).

* Good, because directly usable in OpenAPI 3.1 paths without wrapping
* Good, because Redocly's primary target
* Bad, because not a standalone schema dialect — cannot be used independently of an OpenAPI document
* Bad, because OpenAPI-specific keywords (`discriminator`, `xml`) have no meaning outside OpenAPI context — leaking them into the contract registry creates confusion

### TypeSchema

A strict subset of JSON Schema with additional semantic constraints for code generation.

* Good, because enables precise code generation from schemas
* Bad, because not a widely adopted standard — limited tooling support
* Bad, because Python `jsonschema` does not support TypeSchema natively
* Bad, because does not support JSON-LD contexts or RDF semantics required for VC and ODRL schemas
