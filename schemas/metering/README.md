# schemas/metering — Business Usage Event Schemas

Schemas for metering, rating, and settlement. Separate from observability schemas.

## Structure

| Subdirectory | Contents |
|---|---|
| `source/business/` | Usage record, dimension, quota window, rating rule, rated usage, charge statement, settlement batch |
| `source/transport/` | CloudEvents envelope, event metadata |
| `source/references/` | Agreement, policy, and counterparty reference schemas |
| `bundles/` | Compound bundle documents |
| `examples/valid/` | Valid usage record instances |
| `examples/invalid/` | Instances that must fail |
| `tests/` | Pytest tests |

## Design decisions

- **Business record is transport-independent**: `source/business/` has no CloudEvents dependency. Events can be delivered over Kafka, HTTP, or any other transport.
- **Immutable, append-only**: every usage record must have event time + source provenance. No update operations.
- **Metering ≠ telemetry**: usage records are compliance/billing evidence. OpenTelemetry operational spans are not metering records.
- **Tenant/legal-entity scope is mandatory**: every record must identify the tenant and legal entity for multi-tenancy isolation.
- **Required links**: agreement reference, policy reference, asset reference, counterparty — all mandatory for any chargeable event.
