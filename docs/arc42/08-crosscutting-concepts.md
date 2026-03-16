---
title: "8. Crosscutting Concepts"
summary: "Multi-tenancy, durable execution, canonical model, audit, machine trust, observability, and schema governance — concepts that apply across all platform layers."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

Crosscutting concepts apply uniformly across all platform layers. Violating any of these concepts in any layer is a breaking architectural decision that requires an ADR.

## Multi-Tenancy

Tenant isolation is enforced at three independent layers, each providing defense-in-depth:

**Layer 1 — Identity (Keycloak)**: Each tenant has a dedicated Keycloak realm. Users and service accounts in one realm cannot authenticate to another realm. The realm name is derived deterministically from the `tenant_id`. The `provisioning-agent` creates realms during company onboarding and never reuses realm names.

**Layer 2 — Workflow scoping (Temporal)**: All Temporal workflow IDs are prefixed with `{tenant_id}:`. Workflow visibility queries in the Temporal UI and API use this prefix as the namespace filter. A workflow for `tenant-A` cannot be signalled or cancelled by a request authenticated as `tenant-B`.

**Layer 3 — Database RLS (PostgreSQL)**: Every table that contains tenant-scoped data has a PostgreSQL Row-Level Security policy. The application connects as a non-superuser role. The `SET LOCAL app.tenant_id = $1` session variable is set at the start of every database transaction. RLS policies use `current_setting('app.tenant_id')` as the filter predicate. Even if the API-layer tenant filter is bypassed (e.g., forged `X-Tenant-ID` header), the database returns zero rows for an unauthorized tenant.

**Never**: Application code must never run as the PostgreSQL superuser. Superuser connections bypass RLS. The `tests/tenancy/` suite includes a cross-tenant leakage test that explicitly attempts to read rows for a different tenant and asserts zero results.

## Durable Execution

All multi-step business processes run as Temporal workflows in `procedures/`. The durable execution model has the following implications:

- **Procedure discovery is explicit**: `procedures/` exports `ProcedureDefinition` objects and a shared discovery API. `apps/control-api` and `apps/temporal-workers` consume that registry directly. Worker startup fails fast if zero procedure definitions are discovered; runtime behavior must never depend on `sys.path` mutation or import side effects.
- **Activities are idempotent**: Every activity that has external side effects (Keycloak realm creation, Vault key creation, Postgres INSERT, DPP registry submission) must be idempotent. If an activity is retried after a previous partial success, it must detect the prior completion and return the same result without duplicating the side effect.
- **Workflow code is deterministic**: Temporal replays workflow history to reconstruct state after restarts. Workflow code must be deterministic — no `random`, no `datetime.now()`, no external state reads inside workflow functions. Use `workflow.now()` for time, and pass non-deterministic inputs as activity results.
- **Workflow code is the runbook**: The sequence of activities in a Temporal workflow definition is exactly the sequence an operator would execute manually. Runbooks in `docs/runbooks/` reference the workflow definition for context.
- **Replay testing**: `tests/integration/replay/` contains replay safety tests that execute a workflow, capture the history, and replay it to verify determinism. These tests must pass before any procedure change merges.
- **Time-skipping**: Time-dependent workflows (certificate expiry, metering window close, token refresh) are tested using `WorkflowEnvironment.start_time_skipping()`, which advances the Temporal clock without real-time waiting.

## Procedure Launch and Runtime State

Procedure start is split into two contracts:

- **HTTP request idempotency**: The API persists scoped idempotency records in Postgres under `(tenant_id, procedure_type, idempotency_key)` together with a request fingerprint. Same key plus same fingerprint replays the accepted handle; same key plus different fingerprint returns `409`.
- **Business-process identity**: Each procedure manifest defines the workflow ID template. Entity procedures such as `company-onboarding` therefore reject duplicate active workflows for the same business key even if the caller provides a new HTTP idempotency key.

Runtime status is also split by responsibility:

- **running workflows** expose canonical `ProcedureRuntimeState` via a workflow query so phase and progress are visible immediately
- **Postgres projections** provide the fallback and list-view status model for dashboards, pagination, and degraded-mode reads

## Canonical Model

`core/` is the single source of domain meaning. This principle has specific enforcement rules:

- No adapter, procedure, app, or pack may define a class or type that represents the same concept as a core type with a different structure. If the representation needs to differ for wire compatibility, the adapter must transform between the wire format and the canonical type at the protocol boundary.
- Core domain events (`CompanyOnboarded`, `ContractAgreementFinalized`, `PassportPublished`) are defined in `core/events/` and consumed by procedures. No procedure may define its own event type that duplicates a core event.
- Core invariants (`PassportMustHaveOwner`, `AgreementMustHaveSignedPolicy`) are defined in `core/invariants/` and enforced in procedures before any external side effect is executed.

## Audit and Evidence

Every regulated action emits an evidence artifact:

- **Evidence envelope**: conforms to `schemas/dpp/source/exports/evidence-envelope.schema.json`. Contains: action type, actor (tenant_id + service account), timestamp, payload hash, and a W3C Data Integrity proof signed via Vault Transit.
- **Append-only**: The evidence table in Postgres (`evidence_records`) has no UPDATE or DELETE grants. Evidence is immutable once written. This is enforced at the Postgres role level, not just at the application level.
- **Metering events**: Every agreement-bound data consumption produces a `metering.usage-record` published to Kafka. Records include the agreement ID, tenant ID, asset ID, consumption timestamp, and byte volume. Records accumulate for settlement.
- **Audit log**: Vault's audit backend logs every Transit signing operation, every AppRole login, and every policy evaluation. The audit log is forwarded to the SIEM (outside platform scope).

## Machine Trust Boundaries

Service-to-service authentication follows the machine trust model:

1. **Token acquisition**: The service calls `POST /realms/{realm}/protocol/openid-connect/token` with `grant_type=client_credentials`, `client_id`, and `client_secret`. The `client_secret` is stored in Vault at `secret/data/platform/{service}/keycloak-client-secret` and is rotated monthly.
2. **Token use**: The short-lived JWT (15-minute TTL) is included as `Authorization: Bearer {token}` in all API calls. The token is cached in memory and refreshed 60 seconds before expiry.
3. **Signing**: When a service needs to sign an artifact, it calls the Vault Transit API via the `adapters/infra/vault/` module. The adapter passes the payload bytes and receives the signature bytes. No private key material is handled.
4. **Never**: Service account credentials (client_secret) must never appear in: application logs, OTLP traces, Postgres records, Temporal workflow history, or git-committed configuration files. The `tests/crypto-boundaries/key_references/test_no_raw_keys.py` gate checks for patterns indicating credential leakage.

For browser SSE subscriptions, the control-api can mint a short-lived HMAC
stream ticket. Tickets are scoped to one `workflow_id`, one `tenant_id`, and
audience `procedure-stream`; they are not general bearer substitutes.

## Observability

All platform services emit OTLP (OpenTelemetry Protocol) signals:

- **Traces**: Distributed traces covering all inbound HTTP requests, all Temporal activity executions, all Vault API calls, and all database queries. Trace context propagates via W3C Trace Context headers.
- **Metrics**: OTLP metrics for request latency (p50/p95/p99), Temporal task queue depth, Vault signing operation rate, Kafka consumer lag, and PostgreSQL connection pool utilization.
- **Logs**: Structured JSON logs forwarded via OTLP to Loki. Log records include `trace_id` for correlation.

The OTel Collector gateway enforces **telemetry redaction** before export:

- Attributes matching patterns `.*token.*`, `.*secret.*`, `.*password.*`, `.*key.*` are replaced with `[REDACTED]`.
- HTTP request bodies are never included in traces.
- Span attributes from `Authorization` headers are dropped.

**Alert routing**: Critical alerts (workflow stall, Vault sealed, Postgres unavailable) → PagerDuty. Warning alerts (task queue depth rising, connection pool saturation) → Slack `#platform-alerts`.

The control-api startup path also performs schema readiness checks for Postgres
before enabling durable procedure features. Missing required tables or an
outdated migration level keep the database dependency in degraded mode until
operators complete the rollout.

## Schema Governance

JSON Schema 2020-12 is the house validation dialect for all local schemas. Governance rules:

- **Compatibility classification**: `diff_schema.py` classifies schema changes as `additive` (new optional fields, new enum values), `breaking` (removed required fields, narrowed types, removed enum values), or `compatible` (editorial changes, description updates).
- **Breaking changes require a version bump**: If a schema change is classified as `breaking`, the schema file must be versioned (e.g., `usage-record.schema.v2.json`), the old version retained for the deprecation window (1 major release cycle), and all consumers notified via a handoff note.
- **CI gate**: `make test-schemas` runs `diff_schema.py` against the previous git tag and fails if breaking changes are detected without a version bump.
- **Upstream pins**: Vendor artifacts in `schemas/*/vendor/` must include `provenance.json` with SHA-256 digest. `pin_upstream.py` fetches, verifies, and writes provenance. CI fails if a vendor artifact has no provenance record.
