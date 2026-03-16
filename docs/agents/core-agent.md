---
title: "Core Agent Guidebook"
summary: "Deep guidebook for the core owner, including semantic-kernel invariants and dependency rules."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---
## Purpose

- Own `core/` as the semantic kernel of the control plane. `core/` defines canonical meaning, domain invariants, procedure contracts, and audit primitives that other layers consume.

## Scope

- Define canonical models and shared value objects.
- Encode business invariants and domain services.
- Define ports that adapters implement.
- Define procedure-facing contracts without embedding workflow runtime code.
- Define audit primitives, evidence envelopes, and trust-relevant events.

## Owned Paths

- `core/domains/`
- `core/procedure-runtime/`
- `core/canonical-models/`
- `core/audit/`

## Explicitly Non-Owned Paths

- `apps/`
- `procedures/`
- `adapters/`
- `packs/`
- `schemas/`
- `tests/`
- `infra/`
- `docs/`

## What This Agent Must Read First

1. `core/AGENTS.md`
2. `docs/agents/ownership-map.md`
3. `docs/agents/orchestration-guide.md`
4. `PLANS.md` for any contract or multi-domain work
5. Relevant schema or pack material when canonical terms touch pinned standards

## Architecture Invariants

- `core/` stays framework-light. Prefer pure domain code, interfaces, explicit contracts, and small shared primitives.
- Adapters do not belong in `core/`.
- Workflow engines, Temporal details, and runtime registrations do not belong in `core/`.
- `core/` must not import app runtimes, SDK-specific infrastructure, transport clients, or deployment packaging.
- Canonical meaning lives here once. Packs may overlay policy or profile requirements, but must not fork core semantics.
- Procedure contracts live here when they define business intent, input semantics, result semantics, or evidence shape.

## Subdirectory-By-Subdirectory Responsibilities

### `core/canonical-models`

- Holds shared value objects, identifiers, enums, document envelopes, and canonical terms reused across domains.
- Defines the language that adapters map into and procedures coordinate around.
- Must stay stable and additive where possible because nearly every other root depends on it.

### `core/procedure-runtime`

- Defines procedure-facing contracts that are independent of a specific workflow engine.
- Holds retry semantics, manual-review markers, evidence envelopes, and state transition contracts that procedures consume.
- Does not hold Temporal SDK code, worker registration, or runtime composition.

### `core/audit`

- Defines audit event shapes, evidence envelopes, trust-boundary markers, and operator accountability records.
- Provides shared primitives for immutable evidence references and compliance-oriented traceability.
- Must not be reduced to logging helpers; it owns audit semantics, not sink implementation.

### `core/domains/onboarding`

- Models company onboarding intent, tenant intake, initial eligibility, and bootstrap prerequisites.
- Provides the canonical business meaning consumed by `procedures/company-onboarding`.

### `core/domains/operator-access`

- Models operator roles, least-privilege boundaries, administrative delegation, and public-versus-operator surfaces.
- Defines constraints that `apps/web-console` and `apps/control-api` must enforce through runtime integration.

### `core/domains/tenant-topology`

- Models tenants, subtenants, delegations, environment boundaries, and topology lineage.
- Provides the semantic foundation for delegation procedures and multi-tenant verification.

### `core/domains/machine-trust`

- Models keys, certificates, DIDs, wallet trust references, vault-backed key handles, and issuance intent.
- Owns trust semantics, never raw secret persistence implementations.

### `core/domains/twins`

- Models digital twin concepts, AAS-linked entities, submodel references, twin publication intent, and twin lifecycle state.
- Does not contain AAS server clients or BaSyx-specific wire models.

### `core/domains/schema-mapping`

- Models mappings between enterprise source systems, canonical models, AAS/DPP schema targets, and validation intent.
- Keeps mapping semantics independent of specific ETL tools or adapter transports.

### `core/domains/policies`

- Models business-level governance intent, access constraints, usage purposes, obligations, and policy translation inputs.
- Does not encode EDC or Gaia-X wire-level policy documents directly.

### `core/domains/contracts`

- Models offer, negotiation, agreement, revocation, and contract evidence semantics across ecosystems.
- Provides the canonical abstraction that adapters map protocol-specific negotiations into.

### `core/domains/metering-finops`

- Models usage metering, transfer accounting, billable units, shared-cost attribution, and evidence needed for finops flows.
- Stays independent of any single connector or telemetry backend.

### `core/domains/compliance`

- Models regulatory requirements, evidence obligations, gap status, control objectives, and pack overlays for ESPR, battery passport, and similar regimes.
- Keeps regulation logic explicit without embedding transport or UI concerns.

### `core/domains/observability`

- Models canonical operational signals, health states, SLO-relevant events, and cross-cutting telemetry semantics.
- Does not own metrics exporters or telemetry sinks.

## Allowed Dependencies

- `schemas/` for pinned standard vocabulary and machine-readable artifacts that inform canonical terms
- `docs/` as the explanation layer for ADRs, architecture, and compliance mapping
- Intra-`core/` dependencies only when they preserve a clear semantic hierarchy:
  - `canonical-models` may be imported by every domain
  - `audit` may be imported by every domain
  - foundational domains may be imported by dependent domains with explicit boundaries

## Forbidden Shortcuts

- Do not import adapter SDKs, HTTP clients, ORM models, Helm values, or workflow runtime types.
- Do not place workflow steps or activity orchestration inside domain services.
- Do not let a domain couple directly to a specific ecosystem profile when the semantics are broader.
- Do not move business semantics into schema artifacts to avoid writing canonical models.
- Do not bypass audit semantics with ad hoc log strings.

## Build / Implementation Order

1. Shared primitives and identifiers in `core/canonical-models`
2. Audit primitives and evidence envelopes in `core/audit`
3. Procedure-facing semantic contracts in `core/procedure-runtime`
4. Foundational domains:
   - `onboarding`
   - `operator-access`
   - `tenant-topology`
   - `machine-trust`
5. Dependent domains:
   - `twins`
   - `schema-mapping`
   - `policies`
   - `contracts`
   - `metering-finops`
   - `compliance`
   - `observability`

## Required Tests / Verification

- Existing structural checks:
  - `find core -maxdepth 2 -type d | sort`
  - `test -f core/AGENTS.md`
  - `test -f docs/agents/core-agent.md`
- Expected command once scaffolded: `make test-core`
- Expected command once scaffolded: `pytest tests/unit -k core`
- Expected command once scaffolded: `pytest tests/tenancy -k core`
- Expected command once scaffolded: `pytest tests/crypto-boundaries -k trust`

## Required Docs Updates

- Update `docs/adr/` when invariants or boundary decisions change.
- Update `docs/arc42/` when core architecture, dependencies, or semantic ownership changes.
- Update `docs/compliance-mappings/` when compliance semantics or evidence models change.
- Update `docs/agents/core-agent.md` and `core/AGENTS.md` when domain boundaries move.

## Common Failure Modes

- Canonical models start mirroring vendor DTOs.
- Domain code depends on workflow runtime or adapter clients.
- Compliance semantics drift into pack-only definitions and become invisible to core consumers.
- Audit is treated as log formatting instead of evidence semantics.
- Multiple domains redefine the same identifier or lifecycle state with subtle differences.

## Handoff Contract

- List canonical models added or changed.
- List domains touched and the invariants they now enforce.
- Record new ports or procedure contracts required from neighboring owners.
- State audit or evidence implications.
- Report verification run and docs updated.

## Done Criteria

- Core code remains framework-light and runtime-agnostic.
- Canonical meaning is encoded once and referenced by dependent layers.
- No adapter, workflow engine, or app runtime types leak into `core/`.
- Foundational and dependent domain ordering remains clear.
- Audit and compliance semantics are explicit where affected.

## Example Prompts For This Agent

- "Add a canonical contract state model in `core/domains/contracts` for agreement revocation without introducing DSP wire types."
- "Define machine-trust semantics for wallet bootstrap in `core/domains/machine-trust` and update audit evidence shapes."
- "Refine tenant topology invariants needed by delegated tenant workflows and document the downstream procedure dependency."
