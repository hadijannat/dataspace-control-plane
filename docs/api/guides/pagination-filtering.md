---
title: "Pagination and Filtering Guide"
summary: "Query parameter conventions for paginated control-api list endpoints, including tenant scoping and procedure status filters."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

The control-api uses offset pagination for list endpoints and keeps filtering
explicit in query parameters. The current v1 surface exposes paginated list
responses for operator-facing tenant and procedure queries.

## Shared Pagination Contract

List endpoints return a stable envelope:

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

The shared semantics come from `PaginatedResponse[T]` in
`apps/control-api/app/api/schemas/common.py`.

| Parameter | Type | Default | Bounds | Meaning |
| --- | --- | --- | --- | --- |
| `limit` | integer | `50` | `1..200` | Maximum number of records to return |
| `offset` | integer | `0` | `>= 0` | Number of records to skip before returning items |

## Operator Tenant Listing

```http
GET /api/v1/operator/tenants/?limit=25&offset=50
Authorization: Bearer {token}
```

Tenant visibility is authorization-aware:

- `dataspace-admin` principals can list all tenants.
- non-admin principals only see tenants present in their token-scoped access
  set.
- a principal with no visible tenants receives an empty page, not an error.

## Operator Procedure Listing

```http
GET /api/v1/operator/procedures/?tenant_id=tenant-acme&status=running&limit=20&offset=0
Authorization: Bearer {token}
```

Additional procedure-specific filters:

| Parameter | Type | Meaning |
| --- | --- | --- |
| `tenant_id` | string | Required tenant scope for the read-model query |
| `status` | string | Optional lowercase status filter, normalized before the read-model query |

The procedure list endpoint returns workflow snapshots derived from the
read-model projection. Use the workflow stream URL from an accepted response if
you need near-real-time updates instead of polling a filtered list.

## Recommended Client Pattern

For operator UIs, keep `limit` small and advance with `offset` only after the
user asks for more data. For automation, prefer the status endpoint or SSE
stream over scanning the paginated procedure list for a single workflow.
