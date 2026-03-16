---
title: "Idempotency Guide"
summary: "Idempotent procedure-start semantics for the current control-api implementation, including TTL and operator versus public behavior."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

Idempotency currently applies to the workflow-start endpoints, not to every
mutation route in the conceptual platform design.

## Covered Endpoints

| Endpoint | Where the key lives | Cached result |
| --- | --- | --- |
| `POST /api/v1/operator/procedures/start` | request body `idempotency_key` | previously accepted `ProcedureHandleDTO` |
| `POST /api/v1/public/procedures/start` | `Idempotency-Key` header or body `idempotency_key` | previously accepted `AcceptedResponse` |

For the public start endpoint, the header wins over the body when both are
provided.

## Store Semantics

The current implementation uses the in-process `IdempotencyStore` in
`apps/control-api/app/services/idempotency.py`.

- default TTL is 24 hours (`86400` seconds)
- cached values are stored after a successful accepted start response
- expired entries are evicted lazily on read
- the scaffold is process-local, so multi-replica deployments need a shared
  backend before idempotency becomes cluster-wide

## What Gets Replayed

Duplicate requests return the original accepted workflow handle fields rather
than starting a second workflow:

- `workflow_id`
- `status`
- `poll_url`
- `stream_url`
- `correlation_id` when available

## Current Limitations

- there is no explicit in-flight collision state in the scaffold
- cache scope is the raw idempotency key within the process-local store, not yet
  a durable `{tenant, route, key}` composite persisted in shared storage
- non-start endpoints do not currently participate in the same mechanism

Treat this as a stable caller convenience for the current start routes, not yet
as the final platform-wide idempotency model.
