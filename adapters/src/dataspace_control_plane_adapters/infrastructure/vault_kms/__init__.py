"""Vault KMS infrastructure adapter.

Implements machine_trust/ports.py SignerPort via Vault Transit engine.
Provides PKI certificate lifecycle via Vault PKI engine.
Raw private key material never leaves Vault; Python code only handles references.
"""
from __future__ import annotations
