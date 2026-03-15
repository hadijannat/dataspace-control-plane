"""
tests/crypto-boundaries/conftest.py
Proves the platform's trust model and key custody boundaries.

Invariants:
- No raw private key material is persisted in Postgres.
- No operator-facing API returns PEM/key bytes.
- Only key references or aliases flow through domain and procedure state.
- Revocation and rotation paths work when old key refs exist in historical records.

Requires: Vault container (vault_container fixture), --live-services flag.
"""
from __future__ import annotations
