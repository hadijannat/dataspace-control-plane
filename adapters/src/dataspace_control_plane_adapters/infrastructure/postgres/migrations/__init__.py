"""Database migration SQL files for the PostgreSQL adapter.

Migrations follow the Flyway naming convention: ``V{number}__{description}.sql``.
The migration runner (e.g. Flyway, Liquibase, or a custom runner using advisory
locks from ``locks.py``) applies these in version order.

Invariants
----------
- Migrations are append-only: never modify an existing migration file.
- Every DDL change adds a new ``V{N+1}__*.sql`` file.
- Row-level security is enabled on all multi-tenant tables.
"""
