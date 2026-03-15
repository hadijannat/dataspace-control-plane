# Schema Family: `metering`

> Business-usage event, rated usage, charge statement, and settlement schemas — independent of transport. CloudEvents envelope for event-bus delivery.

**Family version:** 1.0.0  
**Validation dialect:** `https://json-schema.org/draft/2020-12/schema`  
**Effective from:** 2026-03-14  

## Upstream Standards

- **CloudEvents 1.0** 1.0  
  https://cloudevents.io/spec/cloudevents/
- **OpenTelemetry Semantic Conventions** 1.24.0  
  https://opentelemetry.io/docs/specs/semconv/

## Local Source Schemas

## Published Bundles

- `bundles/agreement-ref.bundle.schema.json`
- `bundles/charge-statement.bundle.schema.json`
- `bundles/cloudevents-envelope.bundle.schema.json`
- `bundles/counterparty-ref.bundle.schema.json`
- `bundles/event-metadata.bundle.schema.json`
- `bundles/policy-ref.bundle.schema.json`
- `bundles/quota-window.bundle.schema.json`
- `bundles/rated-usage.bundle.schema.json`
- `bundles/rating-rule.bundle.schema.json`
- `bundles/settlement-batch.bundle.schema.json`
- `bundles/usage-dimension.bundle.schema.json`
- `bundles/usage-record.bundle.schema.json`

| File | Title | Description |
|------|-------|-------------|
| `source/business/charge-statement.schema.json` | Charge Statement | Aggregated billing statement for a tenant over a billing period — the sum of rated usage records. In |
| `source/business/quota-window.schema.json` | Quota Window | A time-bounded quota constraint on a usage dimension for a tenant or agreement. Tracks the limit, co |
| `source/business/rated-usage.schema.json` | Rated Usage | The result of applying a rating rule to a usage record — captures the monetary value assigned to mea |
| `source/business/rating-rule.schema.json` | Rating Rule | Defines how a usage dimension is priced — flat rate, tiered, or formula-based — and which agreement, |
| `source/business/settlement-batch.schema.json` | Settlement Batch | A settlement batch groups one or more charge statements for bulk financial settlement. Represents th |
| `source/business/usage-dimension.schema.json` | Usage Dimension | A single measurable quantity within a usage record — e.g. bytes transferred, API calls made, CPU sec |
| `source/business/usage-record.schema.json` | Usage Record | Immutable record of a single measurable dataspace usage event. Every usage record captures who (tena |
| `source/references/agreement-ref.schema.json` | Agreement Reference | Reference to the ODRL agreement (contract) that governs a usage event. Every usage record must trace |
| `source/references/counterparty-ref.schema.json` | Counterparty Reference | Identifies the other party in a dataspace usage event — the provider (for consumer-side metering) or |
| `source/references/policy-ref.schema.json` | Policy Reference | Reference to the ODRL policy offer that was accepted to create an agreement. Provides lineage from u |
| `source/transport/cloudevents-envelope.schema.json` | CloudEvents Metering Envelope | CloudEvents 1.0 wrapper for a metering usage-record payload. Wraps the business record for event-bus |
| `source/transport/event-metadata.schema.json` | Metering Event Metadata | Operational metadata attached to a metering event for routing, deduplication, and tracing. Separate  |

## CI Gates

    python schemas/tools/validate.py --family metering
    pytest tests/unit -k metering_schemas

---
*Generated 2026-03-15 by `schemas/tools/generate_docs.py`*
