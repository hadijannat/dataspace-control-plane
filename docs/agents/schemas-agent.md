---
title: "Schemas Agent Guidebook"
summary: "Deep guidebook for the schemas owner, including artifact provenance and validation responsibilities."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---
## Purpose

- Own `schemas/` as the machine-readable artifact registry for pinned upstream artifacts, repo-authored schemas, derived bundles, examples, and provenance metadata.

## Scope

- Store source standards and vendor artifacts.
- Author local validation schemas.
- Produce derived bundles or examples that other layers consume.
- Maintain provenance and lock information for deterministic validation.

## Owned Paths

- `schemas/aas`
- `schemas/odrl`
- `schemas/vc`
- `schemas/dpp`
- `schemas/metering`
- `schemas/enterprise-mapping`

## Explicitly Non-Owned Paths

- `core/`
- `procedures/`
- `adapters/`
- `apps/`
- `packs/`
- `tests/`
- `infra/`
- `docs/`

## What This Agent Must Read First

1. `schemas/AGENTS.md`
2. `docs/agents/ownership-map.md`
3. `docs/agents/orchestration-guide.md`
4. `PLANS.md` for schema family or validation-dialect changes
5. Relevant canonical models in `core/` and pack overlays in `packs/`

## Architecture Invariants

- `schemas/` stores artifacts and validation rules, not business meaning.
- Use JSON Schema 2020-12 for repo-authored validation schemas unless a pinned upstream artifact requires another dialect.
- Keep JSON-LD contexts, vocabularies, and upstream normative artifacts pinned and provenance-tracked.
- Distinguish source or vendor artifacts, local authored artifacts, derived bundles, and examples.
- Every repo-authored schema family needs positive examples and negative examples.

## Subdirectory-By-Subdirectory Responsibilities

### `schemas/aas`

- Native source standards involved: Asset Administration Shell, submodel descriptors, related IDTA artifacts
- Source versus local versus derived: pin upstream AAS or IDTA artifacts, author local constraint schemas for repo usage, derive bundles or examples for procedure and adapter validation
- Belongs here, not in canonical models: machine-readable AAS structures, validation documents, pinned contexts
- Validation expectations: validate descriptor shapes, endpoint references, and profile subsets used by twin and DPP flows
- Example requirements: valid twin and submodel examples plus negative cases for missing identifiers or invalid endpoint encoding

### `schemas/odrl`

- Native source standards involved: ODRL, DSP policy payloads, ecosystem-specific ODRL profiles
- Source versus local versus derived: pin upstream contexts or profile artifacts, author local validation envelopes or examples for supported profiles, derive pack-aware test bundles
- Belongs here, not in canonical models: policy JSON-LD structures and profile validation artifacts
- Validation expectations: validate JSON-LD structure, profile identifiers, allowed constraints, and obligations
- Example requirements: valid profile examples plus negative cases for missing context, unsupported constraint vocabulary, or invalid profile bindings

### `schemas/vc`

- Native source standards involved: Verifiable Credentials Data Model, DID-linked credential envelopes, ecosystem trust profile artifacts
- Source versus local versus derived: pin upstream VC and trust profile artifacts, author local validation wrappers where needed, derive example credential bundles
- Belongs here, not in canonical models: credential and proof document shapes
- Validation expectations: validate credential structure, issuer and subject fields, proof envelope presence, and pinned context usage
- Example requirements: valid membership or compliance credential examples plus negative cases for missing issuer or invalid context

### `schemas/dpp`

- Native source standards involved: DPP-oriented JSON-LD or AAS-linked structures, ESPR and battery-passport artifact sets
- Source versus local versus derived: pin regulatory or standards artifacts, author local validation profiles for repo-supported DPP variants, derive product-category bundles
- Belongs here, not in canonical models: DPP document structures, registry payload validation, example bundles
- Validation expectations: validate required sections, identifiers, access-tier annotations, and regulated field presence
- Example requirements: valid DPP documents for at least one product category plus negative cases for missing mandatory regulated fields

### `schemas/metering`

- Native source standards involved: local or ecosystem metering models, usage reporting schemas, telemetry bundle definitions
- Source versus local versus derived: likely repo-authored with pinned references where external standards apply, plus derived reporting bundles
- Belongs here, not in canonical models: metering payload structures, not metering business semantics
- Validation expectations: validate units, timestamps, attribution keys, and evidence references
- Example requirements: valid usage batch examples plus negative cases for malformed units or missing attribution

### `schemas/enterprise-mapping`

- Native source standards involved: local mapping artifacts informed by SAP, Teamcenter, SQL, object storage, or other enterprise sources
- Source versus local versus derived: source-system metadata stays as pinned or recorded input, local mapping specs are authored here, derived mapping bundles support procedures or adapters
- Belongs here, not in canonical models: mapping documents, schema transformation specs, example mapping manifests
- Validation expectations: validate source references, target canonical or AAS bindings, required transformation metadata
- Example requirements: valid mapping manifests plus negative cases for unresolved source fields or unsupported target bindings

## Allowed Dependencies

- `core/` for canonical terms and identifiers referenced by schemas
- `packs/` for ecosystem or regulatory overlays that change validation profiles
- `tests/` for validation, compatibility, and negative-example gates
- `docs/` for schema catalog and operator-facing artifact explanation

## Forbidden Shortcuts

- Do not encode business rules only in schema files and omit the semantic model in `core/`.
- Do not leave upstream artifacts unpinned or without provenance.
- Do not mix vendor examples, local schemas, and derived bundles without clear labels.
- Do not publish JSON-LD context dependencies that require runtime network resolution.
- Do not add schema families without positive and negative examples.

## Build / Implementation Order

1. Identify the source standard or upstream artifact to pin.
2. Record provenance and lock information.
3. Author local validation schemas or derived bundles as needed.
4. Add positive examples and negative examples.
5. Connect pack-specific overlays or profile variants.
6. Add validation tests and compatibility references.
7. Update docs catalogs and owner guidance.

## Required Tests / Verification

- Existing structural checks:
  - `find schemas -maxdepth 2 -type d | sort`
  - `test -f schemas/AGENTS.md`
  - `test -f docs/agents/schemas-agent.md`
- Expected command once scaffolded: `make test-schemas`
- Expected command once scaffolded: `pytest tests/unit -k schemas`
- Expected command once scaffolded: `pytest tests/compatibility -k schema`
- Expected command once scaffolded: `pytest tests/integration -k validation`

## Required Docs Updates

- Update `docs/api/` when schema artifacts back public contracts or machine-readable API surfaces.
- Update `docs/compliance-mappings/` when regulatory schema bundles or validation profiles change.
- Update `docs/arc42/` when artifact strategy or provenance rules change.
- Update `docs/agents/schemas-agent.md` and `schemas/AGENTS.md` when schema family ownership changes.

## Common Failure Modes

- Canonical semantics drift into validation schemas and become invisible to domain review.
- Upstream contexts or artifacts are referenced remotely and later change.
- Negative examples are omitted, leaving validation boundaries unclear.
- Pack overlays and schema variants are mixed without explicit versioning or provenance.
- Enterprise mappings are treated as one-off adapter code instead of reusable artifacts.

## Handoff Contract

- Report schema families changed and whether artifacts are source, local, or derived.
- List provenance or lock updates.
- Identify positive and negative examples added or changed.
- State affected packs, adapters, procedures, or public contracts.
- Report verification run and docs updated.

## Done Criteria

- Repo-authored schemas use JSON Schema 2020-12 by default where applicable.
- Pinned upstream artifacts and JSON-LD contexts have provenance.
- Business meaning remains in `core/`.
- Example and negative-example coverage exists for each new or changed family.
- Downstream docs and compatibility notes are updated.

## Example Prompts For This Agent

- "Add a validation bundle under `schemas/dpp` for a battery-passport document and include negative examples."
- "Pin the ODRL profile artifacts needed by `packs/catenax` and document provenance in `schemas/odrl`."
- "Create an enterprise mapping schema for SAP-to-canonical twin publication and note the downstream adapter dependency."
