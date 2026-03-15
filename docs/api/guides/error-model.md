---
title: "Error Model Guide"
summary: "RFC 7807 Problem Details error format, error type URIs, extension fields, and code examples for all control-api error responses."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Error Model Guide

All control-api error responses use [RFC 7807 Problem Details for HTTP APIs](https://datatracker.ietf.org/doc/html/rfc7807). The `Content-Type` header on error responses is `application/problem+json`.

## Problem Details Format

```json
{
  "type": "/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "detail": "Field 'legalEntityId' must match pattern '^BPNL[0-9A-Z]{12}$'.",
  "instance": "/api/v1/companies",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "code": "COMPANY_INVALID_BPN",
  "validationErrors": [
    {
      "field": "legalEntityId",
      "message": "Must match pattern '^BPNL[0-9A-Z]{12}$'",
      "value": "INVALID-BPN"
    }
  ]
}
```

### Standard Fields (RFC 7807)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string (URI) | Yes | URI reference identifying the problem type. Relative URIs are resolved against the API base URL. |
| `title` | string | Yes | Short, human-readable summary. Should be constant for the same `type` across occurrences. |
| `status` | integer | Yes | HTTP status code. Must match the response HTTP status. |
| `detail` | string | Yes | Occurrence-specific human-readable explanation. |
| `instance` | string (URI) | Yes | URI identifying the specific occurrence. Typically the request path. |

### Extension Fields

| Field | Type | Present when | Description |
|-------|------|-------------|-------------|
| `traceId` | string | Always | OpenTelemetry W3C trace ID for correlating with distributed traces in Grafana Tempo or Jaeger |
| `code` | string | Most errors | Platform-specific error code for programmatic handling. Stable across API versions. |
| `validationErrors` | array | 400, 422 | Field-level validation error details (field path, message, invalid value) |
| `workflowError` | object | 500 (workflow) | Temporal workflow failure details: `{workflowId, failedActivity, temporalError}` |
| `retryAfter` | integer | 429 | Seconds until the client may retry (also set in `Retry-After` response header) |

## Error Type URI Table

All `type` values are relative URIs resolved against the API base URL. Clients should match on the `type` URI, not on the `title` string (which may be localized in future).

| Type URI | HTTP status | `code` prefix | Description |
|----------|------------|---------------|-------------|
| `/errors/not-found` | 404 | `*_NOT_FOUND` | The requested resource does not exist within the authenticated tenant |
| `/errors/validation-failed` | 400, 422 | `*_INVALID_*` | Request body or parameters failed schema validation |
| `/errors/authentication-required` | 401 | `AUTH_REQUIRED` | No Bearer token provided or token is malformed |
| `/errors/authentication-expired` | 401 | `AUTH_EXPIRED` | Bearer token has expired (`exp` claim in the past) |
| `/errors/authorization-denied` | 403 | `AUTHZ_*` | Authenticated but insufficient role for this operation |
| `/errors/conflict` | 409 | `*_CONFLICT` | Request conflicts with current resource state (duplicate, invalid lifecycle transition) |
| `/errors/rate-limited` | 429 | `RATE_LIMITED` | Too many requests from this tenant — see `retryAfter` |
| `/errors/workflow-failed` | 500 | `WORKFLOW_*` | A Temporal workflow failed — see `workflowError` for details |
| `/errors/schema-validation-failed` | 422 | `SCHEMA_*` | Payload failed JSON Schema 2020-12 validation against the relevant pack schema |
| `/errors/dependency-unavailable` | 503 | `DEP_*` | An upstream dependency (Vault, Temporal, Postgres) is temporarily unavailable |
| `/errors/idempotency-conflict` | 409 | `IDEM_CONFLICT` | A concurrent request with the same Idempotency-Key is in flight |
| `/errors/tenant-suspended` | 403 | `TENANT_SUSPENDED` | The authenticated tenant has been suspended by the platform operator |

## Example Error Responses

### 401 — Expired token

```json
{
  "type": "/errors/authentication-expired",
  "title": "Authentication Token Expired",
  "status": 401,
  "detail": "The Bearer token expired at 2026-03-14T12:30:00Z. Please obtain a new token.",
  "instance": "/api/v1/companies",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "code": "AUTH_EXPIRED"
}
```

### 422 — Schema validation failure (pack schema)

```json
{
  "type": "/errors/schema-validation-failed",
  "title": "Passport Schema Validation Failed",
  "status": 422,
  "detail": "The passport fields do not satisfy the Battery Passport Annex XIII mandatory field requirements.",
  "instance": "/api/v1/passports/lifecycle-transitions",
  "traceId": "5ce03f4688c45eb7b4df030e1f1f5847",
  "code": "SCHEMA_BATTERY_PASSPORT_ANNEX_XIII",
  "validationErrors": [
    {
      "field": "fields.batteryChemistry",
      "message": "Required field missing (Annex XIII, Section 4.2, public tier)",
      "value": null
    },
    {
      "field": "fields.carbonFootprint.value",
      "message": "Must be a number (kgCO2e/kWh)",
      "value": "not-a-number"
    }
  ]
}
```

### 500 — Temporal workflow failure

```json
{
  "type": "/errors/workflow-failed",
  "title": "Workflow Execution Failed",
  "status": 500,
  "detail": "The DPP export workflow failed during registry submission. The passport is in 'approved' state and can be retried.",
  "instance": "/api/v1/passports/a1b2c3d4-e5f6-7890-abcd-ef1234567890/lifecycle-transitions",
  "traceId": "7ef14g5799d56fc8c5eg141f2g2g6958",
  "code": "WORKFLOW_DPP_EXPORT_FAILED",
  "workflowError": {
    "workflowId": "tenant-acme-001:dpp-export:a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "runId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "failedActivity": "submit_to_dpp_registry",
    "temporalError": "Activity exceeded maximum retry attempts (3). Last error: HTTP 503 from EU DPP Registry."
  }
}
```

### 429 — Rate limited

```json
{
  "type": "/errors/rate-limited",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "This tenant has exceeded the rate limit of 100 requests per minute on /api/v1/usage-events.",
  "instance": "/api/v1/usage-events",
  "traceId": "8fg25h6800e67gd9d6fh252g3h3h7069",
  "code": "RATE_LIMITED",
  "retryAfter": 47
}
```

## Client Error Handling Pattern

```python
import httpx

class ControlApiError(Exception):
    def __init__(self, problem: dict):
        self.type = problem["type"]
        self.title = problem["title"]
        self.status = problem["status"]
        self.detail = problem["detail"]
        self.trace_id = problem.get("traceId")
        self.code = problem.get("code")
        super().__init__(f"[{self.status}] {self.type}: {self.detail}")

class ValidationError(ControlApiError):
    def __init__(self, problem: dict):
        super().__init__(problem)
        self.validation_errors = problem.get("validationErrors", [])

async def handle_api_response(response: httpx.Response) -> dict:
    if response.status_code < 400:
        return response.json()

    problem = response.json()
    error_type = problem.get("type", "")

    if error_type in ("/errors/validation-failed", "/errors/schema-validation-failed"):
        raise ValidationError(problem)
    elif error_type == "/errors/rate-limited":
        retry_after = problem.get("retryAfter", 60)
        raise RateLimitError(problem, retry_after)
    else:
        raise ControlApiError(problem)
```
