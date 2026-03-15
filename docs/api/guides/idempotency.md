---
title: "Idempotency Guide"
summary: "How the Idempotency-Key header works, scope, TTL, and safe retry patterns for control-api mutation endpoints."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Idempotency Guide

All `POST`, `PATCH`, and `DELETE` endpoints on the control-api support idempotent requests via the `Idempotency-Key` header. This enables clients to safely retry failed requests without duplicating side effects.

## How It Works

When a mutation request includes an `Idempotency-Key` header:

1. **First request (key not seen)**: The server processes the request normally, stores the response (status code + body), and associates it with the idempotency key for 24 hours.
2. **Subsequent requests (same key, same tenant)**: The server returns the stored response immediately without re-executing the operation. The HTTP status code and response body are identical to the original response.
3. **Concurrent requests (same key, request in flight)**: If a second request with the same key arrives while the first is still being processed, the server returns `409 Conflict` with a Problem Details body indicating a key collision.

## Key Format

The `Idempotency-Key` value must be a UUID v4:

```http
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

Do not use sequential integers, timestamps, or deterministic values as idempotency keys — these are likely to collide across different logical operations.

## Key Scope

Idempotency keys are scoped **per tenant, per endpoint method + path**. The same key value used for `POST /companies` and `POST /passports` does not conflict — they are treated as distinct entries.

Key scope: `{tenant_id}:{method}:{path}:{idempotency_key}`

| Scenario | Result |
|---------|--------|
| Same key, same tenant, same endpoint | Returns cached response |
| Same key, different tenant | Treated as a new request (different scope) |
| Same key, same tenant, different endpoint | Treated as a new request (different scope) |
| Same key, same tenant, same endpoint, after 24h | Key expired — treated as a new request |

## Client Responsibility

- **Generate one key per logical operation**, not per HTTP retry. If you retry a request that received a network timeout, use the **same idempotency key** as the original request.
- **Do not reuse keys** across different logical operations. Using the same key for a company registration and a passport creation will return the company registration response for the passport creation endpoint.

## Safe Retry Pattern

```python
import uuid
import httpx
import time

async def register_company_with_retry(
    client: httpx.AsyncClient,
    payload: dict,
    max_retries: int = 3,
) -> dict:
    # Generate ONE idempotency key for this logical operation
    idempotency_key = str(uuid.uuid4())

    last_error = None
    for attempt in range(max_retries):
        try:
            response = await client.post(
                "/api/v1/companies",
                json=payload,
                headers={
                    "Authorization": f"Bearer {await get_token()}",
                    "Idempotency-Key": idempotency_key,  # Same key on every retry
                },
                timeout=30.0,
            )

            # 202 Accepted: workflow started (first request or cached)
            if response.status_code in (201, 202):
                return response.json()

            # 4xx client errors are not retryable
            if 400 <= response.status_code < 500:
                response.raise_for_status()

            # 5xx server errors: retry with backoff
            last_error = httpx.HTTPStatusError(
                f"Server error {response.status_code}",
                request=response.request,
                response=response,
            )

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            last_error = e

        if attempt < max_retries - 1:
            # Exponential backoff: 1s, 2s, 4s
            wait = 2 ** attempt
            time.sleep(wait)

    raise last_error
```

## Response Caching Behavior

The idempotency store caches the **complete HTTP response**: status code, headers (except `Date` and `X-Request-Id`), and body. This means:

- A `202 Accepted` with a workflow handle is cached — retrying returns the same workflow handle, allowing the client to poll the same `statusUrl`.
- A `400 Bad Request` is **not cached** — the server does not cache error responses. A retry with the same key after a validation error will re-process the request.
- A `201 Created` is cached — retrying does not create a duplicate resource.

## Inspecting Idempotency Key Status

To check whether an idempotency key is still cached (useful for debugging):

```http
GET /api/v1/internal/idempotency/{idempotency_key_uuid}
Authorization: Bearer {token}
```

Returns `{"status": "cached", "cachedAt": "...", "expiresAt": "..."}` or `404` if the key is not found or has expired.

!!! note "Internal endpoint"
    `/api/v1/internal/idempotency/` is an unstable internal endpoint. Do not use it in production client code.
