# schemas/enterprise-mapping — Mapping DSL

JSON Schema DSL for describing source data models, field mappings, transform steps, lineage, and execution results.

## Structure

| Subdirectory | Contents |
|---|---|
| `source/mapping/` | Source model, target model ref, mapping spec, field mapping, transform step, lineage graph, approval, confidence |
| `source/source-kinds/` | Source-kind references: OData CSDL, SQL model, event schema, object metadata |
| `source/execution/` | Mapping run and result schemas |
| `bundles/` | Compound bundles |
| `examples/valid/` | Valid mapping specs |
| `examples/invalid/` | Instances that must fail |
| `tests/` | Pytest tests |

## Design decisions

- **DSL is JSON Schema-based**: mapping specs are JSON documents validated by JSON Schema.
- **Source-native models are referenced, not inlined**: an OData CSDL ref points to the CSDL document; it doesn't duplicate the type system inside our DSL.
- **Lineage is mandatory**: every target field mapping must declare its lineage (source fields, transform, confidence, approval state).
- **Execution is separate from definition**: `mapping-spec.schema.json` defines the intent; `mapping-run.schema.json` records what actually happened.
- **OData CSDL is preserved**: source-native OData model metadata is kept as-is and referenced by the DSL.

## OData 4.01 note

OData 4.01 defines REST-based data services with a formal CSDL data model and a JSON representation. Use `odata-csdl-ref.schema.json` to reference CSDL documents from mapping specs without flattening them.
