---
title: "Idempotency Guide"
summary: "Durable procedure-start idempotency semantics, including scoped keys, request fingerprints, and business-key workflow identities."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

Idempotency applies to the workflow-start endpoints. It prevents duplicate HTTP
starts; it does not replace the business-key workflow identity defined by each
procedure manifest.

## Covered Endpoints

| Endpoint | Where the key lives | Cached result |
| --- | --- | --- |
| `POST /api/v1/operator/procedures/start` | request body `idempotency_key` | previously accepted `ProcedureHandleDTO` |
| `POST /api/v1/public/procedures/start` | `Idempotency-Key` header or body `idempotency_key` | previously accepted `AcceptedResponse` |

For the public start endpoint, the header wins over the body when both are
provided.

## Store Semantics

The current implementation uses the durable Postgres-backed
`PostgresIdempotencyRepository`.

- scope key: `(tenant_id, procedure_type, idempotency_key)`
- request fingerprint: canonicalized workflow input plus the caller's auth
  scope
- stored fields: `workflow_id`, `run_id`, accepted response JSON, status, and
  timestamps
- storage table: `http_idempotency_keys`

The acquire/finalize flow is atomic at the row level:

- same scoped key + same fingerprint → replay the original accepted response
- same scoped key + different fingerprint → `409 Conflict`
- new scoped key → reserve the row, start the workflow, then finalize with the
  run metadata

## What Gets Replayed

Duplicate requests return the original accepted workflow handle fields rather
than starting a second workflow:

- `workflow_id`
- `status`
- `poll_url`
- `stream_url`
- `correlation_id` when available

## Business-Key Workflow IDs

Workflow IDs are generated from the procedure definition, not the idempotency
key. For `company-onboarding`, the workflow identity is:

```text
company-onboarding:{tenant_id}:{legal_entity_id}
```

That means there are two distinct duplicate protections:

- HTTP idempotency stops duplicate start requests from the same caller intent
- Temporal workflow identity stops duplicate entity workflows for the same
  business key

If a caller submits a new idempotency key for a workflow that is already active
for the same business key, the API returns `409`.

## Current Boundaries

- non-start endpoints do not currently participate in the same mechanism
- the operator and public start endpoints share the same underlying
  idempotency and workflow identity rules, but expose different accepted
  response shapes
- replay returns the original accepted handle, not a synthetic "duplicate"
  envelope

Treat this as the stable start-route contract for the current control plane.
