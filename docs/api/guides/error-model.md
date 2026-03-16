---
title: "Error Model Guide"
summary: "Current error response behavior for the control-api scaffold, including FastAPI default errors and the custom 500 envelope."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

The current control-api scaffold does **not** yet expose a uniform RFC 7807
Problem Details contract. Error responses currently fall into two families.

## 1. FastAPI and Route-Level Errors

Most 4xx responses come directly from route handlers or FastAPI validation.

Examples:

- `401` from Bearer or stream-ticket validation
- `403` from tenant access checks
- `404` for missing procedures or tenants
- `422` for route-level validation failures

Typical shape:

```json
{
  "detail": "Access to tenant 'tenant-a' is not permitted"
}
```

Validation failures use FastAPI's standard list-style `detail` payload.

## 2. Unhandled Exception Envelope

Unhandled exceptions are converted by `install_exception_handlers()` into a
small JSON envelope:

```json
{
  "code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred",
  "correlation_id": "2c8f0d5f..."
}
```

This shape is used for unexpected `500` responses only.

## Correlation IDs

When request correlation is available, the custom `500` envelope echoes it as
`correlation_id`. This is the primary field for joining client-visible failures
to logs and traces in the current scaffold.

## Documented Gap

The human docs previously described a full RFC 7807 contract. That remains a
reasonable future target, but it is not the live API behavior today. Any move
to Problem Details should land together with route handlers, OpenAPI updates,
and client guidance.
