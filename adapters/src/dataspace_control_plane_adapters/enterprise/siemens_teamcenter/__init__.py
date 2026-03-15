"""Siemens Teamcenter read-only export adapter.

Covers BOM extraction, item revision metadata, and linked dataset retrieval.
Uses session-based auth against the Teamcenter REST microservice gateway.
Large exports are chunked for safe resume.
"""
from __future__ import annotations
