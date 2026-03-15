"""
tests/tenancy/conftest.py
Tenancy suite: proves cross-tenant isolation at the database, API, workflow, and search layers.

Requires: PostgreSQL with RLS policies enabled, application roles, seed data.
All tests require --live-services. Run-as-superuser tests are explicitly labeled.
"""
from __future__ import annotations
