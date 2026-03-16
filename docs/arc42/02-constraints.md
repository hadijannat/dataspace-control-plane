---
title: "2. Constraints"
summary: "Technical, regulatory, and organizational constraints that shape the dataspace control plane design."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

Constraints are non-negotiable decisions imposed on the architecture from outside the development team. They differ from architectural decisions (which are choices) in that they cannot be changed without external approval or compliance risk.

## Technical Constraints

| Constraint | Reason |
|-----------|--------|
| **Python 3.12 for all server-side code** | Temporal Python SDK, FastAPI, and the existing packs ecosystem are Python-first. Mixing languages at the server layer would require multi-language SDK maintenance and break test tooling. |
| **Temporal as the only workflow engine** | Durable execution, replay safety, and time-skipping test support are required. Temporal's `WorkflowEnvironment.start_time_skipping()` enables deterministic unit-speed testing of time-sensitive business processes. No custom outbox pattern or Celery-based alternative satisfies the replay guarantee. See [ADR 0002](../adr/0002-adopt-temporal-as-workflow-engine.md). |
| **JSON Schema 2020-12 for all local schemas** | Consistent `$id` and `$ref` resolution model, meta-schema tooling compatibility across Python `jsonschema`, Redocly, and NIST OSCAL validators. All local schemas in `schemas/source/` use 2020-12; vendor-pinned upstream artifacts are exempt. See [ADR 0003](../adr/0003-json-schema-2020-12-as-house-dialect.md). |
| **Vault Transit for all signing operations** | No raw private key material in application state, Temporal workflow history, Postgres, or application logs. Vault Transit is the exclusive signing boundary. See [ADR 0004](../adr/0004-vault-transit-for-signing-keys.md). |
| **Keycloak for all human and machine authentication** | OpenID Connect Authorization Code flow for human operators; `client_credentials` grant for service-to-service machine auth. Keycloak provides realm-per-tenant isolation at the identity layer. No other IdP is supported. |
| **ODRL 2.2 policy format** | Catena-X operating model mandates ODRL 2.2 for all data access contracts. The `packs/catenax/` module enforces this. Non-ODRL policy formats cannot be used for Catena-X data offers. |
| **W3C VC Data Model 2.0 credential format** | DCP protocol mandate for Catena-X credential presentations. All credentials issued by the platform must conform to `schemas/vc/source/envelope/credential-envelope.schema.json`. |
| **AAS Release 25-01** | IDTA standard for Digital Product Passports. Newer releases may introduce breaking schema changes; the platform pins to 25-01 until IDTA publishes a migration guide. |
| **Next.js for web-console** | The operator web console (`apps/web-console/`) is a Next.js application to enable server-side rendering, static export for offline operator kits, and React component ecosystem compatibility. |
| **PostgreSQL with RLS** | Row-Level Security is the final tenant isolation enforcement layer. The platform must never run application code as the PostgreSQL superuser. All tenant tables must have RLS policies enabled. |

## Regulatory Constraints

| Regulation | Scope | Impact on Platform |
|-----------|-------|-------------------|
| **EU Regulation 2023/1542 (Battery Regulation)** | Battery products sold in the EU | Battery Passport required from 2027 (large industrial batteries from 2024). Annex XIII defines the mandatory field list across three access tiers (public, authority, legitimate-interest). |
| **EU Regulation 2024/1781 (ESPR)** | Regulated product categories | Digital Product Passport required. Delegated acts per product category define specific fields — these are not yet published for all categories. `packs/espr_dpp/delegated_acts/` holds a template; it must be updated when acts are published. |
| **GDPR (Regulation 2016/679)** | Personal data in tenant payloads | Tenant payloads may include personal data (operator identities, end-customer battery ownership records). Data minimization, retention limits, and right-to-erasure must be considered in schema design. Personally identifiable fields must not be logged in OTLP traces. |
| **EU AI Act (Regulation 2024/1689)** | ML-assisted enterprise field mapping | If ML/AI models are used to assist enterprise field mapping (`adapters/enterprise/`), AI Act transparency and accuracy requirements may apply. This is a future risk; current mapping is deterministic DSL-based. |
| **Catena-X Operating Model 4.0** | Dataspace participation | Mandates DSP catalog endpoint, DCP credential service, ODRL policy evaluation, and W3C VC-based member onboarding. Non-compliance disqualifies participation. |

## Organizational Constraints

| Constraint | Rationale |
|-----------|-----------|
| **One owner per root directory** | Each top-level directory has exactly one specialist owner. No two owners edit the same root in the same task without explicit prompt authorization. This prevents accidental cross-layer coupling. |
| **Handoff artifact required before agent idle** | Every teammate must write `.claude/handoffs/<dir>.md` before going idle. The idle gate hook enforces this. No wave can close without all handoffs present. |
| **Wave-based build order enforced** | The 4-wave model (foundation-planning → platform-foundation → execution-layer → overlays-hardening) defines which layers can be built simultaneously. Downstream layers cannot be scaffolded before upstream layers provide their ports and schemas. |
| **No raw infrastructure access for application code** | Application pods must not use cluster-admin credentials, database superuser accounts, or Vault root tokens. All access is scoped by Keycloak service account, Vault policy, and database role. |
| **Forbidden zones enforced by hook** | Each owner has an explicit list of directories they must not edit, documented in `docs/agents/ownership-map.md`. The `protect-shared-files` hook prevents accidental cross-boundary edits. |
