"""SAP OData 4.01 metadata-driven source adapter.

Read-only. Fetches $metadata on first use, caches with TTL, then compiles
queries from the model. Supports full-snapshot and watermark-incremental extraction.
"""
from __future__ import annotations
