"""PostgreSQL infrastructure adapter.

Provides:
- asyncpg-backed connection pool with tenant isolation via RLS
- Append-only audit record sink and query
- Negotiation and entitlement repositories with optimistic concurrency
- Operator grant read model
- Transactional outbox writer / poller
- Advisory-lock helpers for migration coordination
"""
