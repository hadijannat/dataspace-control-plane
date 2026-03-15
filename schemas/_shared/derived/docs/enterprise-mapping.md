# Schema Family: `enterprise-mapping`

> Schema DSL for source-model snapshots, field mappings, transform steps, lineage graphs, and mapping execution results — covering OData CSDL, SQL, event, and object-storage sources.

**Family version:** 1.0.0  
**Validation dialect:** `https://json-schema.org/draft/2020-12/schema`  
**Effective from:** 2026-03-14  

## Upstream Standards

- **OData 4.01 Protocol** 4.01  
  https://docs.oasis-open.org/odata/odata/v4.01/odata-v4.01-part1-protocol.html
- **OData 4.01 CSDL JSON** 4.01  
  https://docs.oasis-open.org/odata/odata-csdl-json/v4.01/
- **CloudEvents 1.0** 1.0  
  https://cloudevents.io/spec/cloudevents/

## Local Source Schemas

## Published Bundles

- `bundles/approval.bundle.schema.json`
- `bundles/confidence.bundle.schema.json`
- `bundles/event-schema-ref.bundle.schema.json`
- `bundles/field-mapping.bundle.schema.json`
- `bundles/lineage-graph.bundle.schema.json`
- `bundles/mapping-result.bundle.schema.json`
- `bundles/mapping-run.bundle.schema.json`
- `bundles/mapping-spec.bundle.schema.json`
- `bundles/object-metadata-ref.bundle.schema.json`
- `bundles/odata-csdl-ref.bundle.schema.json`
- `bundles/source-model.bundle.schema.json`
- `bundles/sql-model-ref.bundle.schema.json`
- `bundles/target-model-ref.bundle.schema.json`
- `bundles/transform-step.bundle.schema.json`

| File | Title | Description |
|------|-------|-------------|
| `source/execution/mapping-result.schema.json` | Mapping Result | Detailed result of a mapping run execution — per-field error rates, transform failures, and data qua |
| `source/execution/mapping-run.schema.json` | Mapping Run | Execution record for a single run of a mapping specification. Immutable audit record capturing when  |
| `source/mapping/approval.schema.json` | Mapping Approval State | Approval state for a mapping specification or individual field mapping. Prevents unapproved mappings |
| `source/mapping/confidence.schema.json` | Mapping Confidence Score | Confidence assessment for a mapping specification or individual field mapping. Derived automatically |
| `source/mapping/field-mapping.schema.json` | Field Mapping | A mapping from one or more source fields (with optional transforms) to a single target field. Lineag |
| `source/mapping/lineage-graph.schema.json` | Field Lineage Graph | Lineage record for a target field — captures the source fields, transform function chain, and deriva |
| `source/mapping/mapping-spec.schema.json` | Mapping Specification | A complete mapping specification from a source model to a target model. Defines field mappings, tran |
| `source/mapping/source-model.schema.json` | Source Model Snapshot | A snapshot of a source data model — tables, entities, or event types — at a point in time. The sourc |
| `source/mapping/target-model-ref.schema.json` | Target Model Reference | Reference to the target model that a mapping spec maps into — typically a core/ domain model or a ca |
| `source/mapping/transform-step.schema.json` | Transform Step | A single transform function applied in a mapping pipeline. Captures function identity, input type, o |
| `source/source-kinds/event-schema-ref.schema.json` | Event Schema Reference | Reference to an event source schema — CloudEvents, AsyncAPI, Avro, or JSON Schema. Does not force Cl |
| `source/source-kinds/object-metadata-ref.schema.json` | Object Storage Metadata Reference | Reference to an object storage source — S3-compatible bucket, container, or prefix — where structure |
| `source/source-kinds/odata-csdl-ref.schema.json` | OData CSDL Reference | Reference to an OData 4.01 CSDL (Common Schema Definition Language) document describing the source d |
| `source/source-kinds/sql-model-ref.schema.json` | SQL Model Reference | Reference to a SQL database model (introspected schema metadata). Used when the source is a relation |

## CI Gates

    python schemas/tools/validate.py --family enterprise-mapping
    pytest tests/unit -k enterprise_mapping_schemas

---
*Generated 2026-03-15 by `schemas/tools/generate_docs.py`*
