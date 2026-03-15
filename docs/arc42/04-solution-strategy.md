---
title: "4. Solution Strategy"
summary: "Fundamental architectural bets, rationale, and the constraints each decision addresses."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# 4. Solution Strategy

The solution strategy documents the fundamental architectural bets — the choices that shape the entire design and that would be expensive to reverse. Each decision is stated plainly with its rationale and the constraint or quality goal it addresses.

## Architectural Bets

### 1. Core-First Semantic Layer

**Decision**: All domain meaning is defined once in `core/`. Adapters implement ports to translate external protocols to core types; procedures orchestrate core domain events; packs add overlay rules referencing core types. No layer outside `core/` may redefine what a concept means.

**Rationale**: Industrial dataspaces involve many overlapping protocol formats (DSP JSON-LD, AAS submodel XML, ODRL JSON-LD, DPP JSON, VC JSON-LD). Without a single semantic kernel, each adapter would develop its own interpretation of what "agreement" or "passport" means, creating silent semantic drift. The core-first approach means protocol drift in adapters cannot contaminate business logic in procedures.

**Constraint addressed**: One owner per root; no cross-layer semantic redefinition.

### 2. Packs as Pure Overlays

**Decision**: Regulatory and ecosystem rules live in `packs/` as pure overlays over `core/`. Each pack implements the shared pack interface (manifest, reducer, validators). Packs can be composed; conflicts are declared explicitly in the reducer.

**Rationale**: The platform must simultaneously support Catena-X (ODRL policies, VCs), Gaia-X (Self-Descriptions, trust labels), Battery Passport (Annex XIII tiers), and ESPR DPP (delegated act fields) — and this list will grow. Without the overlay model, every new regulation or ecosystem would require forking core domain logic. Packs allow multiple regulatory regimes to apply to the same canonical model without forking. See [ADR 0005](../adr/0005-packs-as-pure-overlay.md).

**Constraint addressed**: EU Regulation 2023/1542, EU Regulation 2024/1781, Catena-X Operating Model.

### 3. Temporal for All Multi-Step Processes

**Decision**: Every business process with more than one observable step runs as a Temporal workflow. No custom outbox pattern, Celery task chain, or manual saga implementation is permitted.

**Rationale**: Company onboarding touches Keycloak, Vault, Postgres, and the DID registry — if any step fails, the entire process must be restartable from the failed step without duplicating side effects. Temporal's durable execution guarantee provides this without requiring application-level compensating transactions. Workflow code is the runbook: the sequence of activities in a workflow definition is exactly the sequence an operator would follow manually. `WorkflowEnvironment.start_time_skipping()` enables unit-speed testing of time-dependent processes (certificate expiry, metering windows). See [ADR 0002](../adr/0002-adopt-temporal-as-workflow-engine.md).

**Constraint addressed**: Durable execution quality goal; replay safety for audit.

### 4. Vault Transit as the Cryptographic Boundary

**Decision**: No private key material exists outside HashiCorp Vault's Transit engine. All signing (VC proofs, DID documents, evidence artifacts, ODRL agreement seals) is performed via Vault Transit API calls. Keys are created with `exportable=false`.

**Rationale**: Private keys in Postgres, workflow history, or application code create a large blast radius in the event of a database breach or log exfiltration. Vault Transit ensures the signing boundary is auditable (Vault audit log records every signing operation), rotatable (key versioning with rotation window), and never in application state. See [ADR 0004](../adr/0004-vault-transit-for-signing-keys.md).

**Constraint addressed**: Regulatory requirement for tamper-evident evidence; threat model T-KM-01.

### 5. Tenant Isolation at the Database Layer

**Decision**: PostgreSQL Row-Level Security is the final tenant isolation enforcement layer. Every tenant-scoped table has an RLS policy. The application connects as a non-superuser role. API-layer tenant filtering is defense-in-depth, not the primary guard.

**Rationale**: A misconfigured API middleware or forged `X-Tenant-ID` header must not expose another tenant's data. RLS ensures that even if the API layer is completely bypassed, the database query returns zero rows for unauthorized tenants. The `tests/tenancy/` suite verifies RLS correctness on every schema migration.

**Constraint addressed**: Tenant isolation quality goal; threat model T-DI-04.

### 6. Schema-First Contracts

**Decision**: JSON Schema 2020-12 families in `schemas/` are the contract registry. All producer outputs (adapter wire models, procedure evidence artifacts, pack export schemas) must validate against the relevant schema before being persisted or transmitted. Breaking schema changes require a version bump and must be detected by `diff_schema.py` in CI.

**Rationale**: Without a schema registry, ad-hoc format changes in one layer silently break consumers in another. The schema-first approach makes contracts explicit, machine-verifiable, and version-controlled. See [ADR 0003](../adr/0003-json-schema-2020-12-as-house-dialect.md).

**Constraint addressed**: Protocol compliance quality goal; regulatory alignment (DPP field completeness).

### 7. Wave-Based Delivery

**Decision**: Development proceeds in 4 waves with mandatory handoff artifacts between waves. Downstream layers cannot be scaffolded before upstream layers provide their ports and schemas. Each wave has assigned specialist owners per root directory.

**Rationale**: In a 9-layer monorepo, accidental cross-layer coupling is the primary delivery risk. The wave model enforces build order at the process level: procedures cannot be written until core/ defines the canonical events they orchestrate; apps cannot be written until procedures/ provides the workflow contracts they invoke. Handoff artifacts make cross-layer dependencies explicit and auditable.

**Constraint addressed**: Organizational constraint on wave order; handoff artifact requirement.
