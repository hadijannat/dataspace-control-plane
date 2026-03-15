"""
tests/chaos/conftest.py
Deterministic failure injection suite.

Uses Toxiproxy to inject latency, resets, and blackholes.
All chaos tests require --live-services and Docker.
Randomized combinations are nightly-only (@pytest.mark.nightly).
"""
from __future__ import annotations
