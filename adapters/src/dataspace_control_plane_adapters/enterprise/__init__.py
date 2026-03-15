"""Enterprise adapter sub-package.

Contains integration adapters for enterprise systems:
- sap_odata: OData 4.01 metadata-driven source adapter for SAP
- siemens_teamcenter: BOM/revision/document export adapter for Teamcenter
- kafka_ingest: Idempotent event ingestion and normalized publishing
- object_storage: S3-compatible streaming object store (AASX, evidence)
- sql_extract: Generic SQL snapshot + watermark + PostgreSQL CDC adapter
"""
from __future__ import annotations
