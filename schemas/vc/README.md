# schemas/vc — Verifiable Credentials

Machine-readable schema family for W3C Verifiable Credentials and Presentations.

## What is here

| Subdirectory | Contents |
|---|---|
| `vendor/w3c/` | Pinned W3C JSON-LD contexts, vocabularies, and status lists |
| `source/envelope/` | Credential and presentation envelope shapes |
| `source/integrity/` | Proof metadata and status-reference schemas |
| `source/status/` | Bitstring status list reference schema |
| `source/profiles/` | Base profile schema for platform-specific credential types |
| `derived/contexts/` | Offline-resolvable context bundles (generated) |
| `derived/vocab/` | Vocab snapshots (generated) |
| `derived/json-schema/` | W3C JSON Schema resources normalized to local dialect |
| `bundles/` | Compound bundle documents for runtime use |
| `examples/valid/` | Instances that must pass validation |
| `examples/invalid/` | Instances that must fail validation |
| `tests/` | Pytest tests for this family |

## Design decisions

- **Offline context resolution**: JSON-LD `@context` values point to `vendor/w3c/` files, not live W3C URLs.
- **Separation of layers**: envelope shape ≠ integrity metadata ≠ credential profile. Each is a separate schema.
- **No proof verification logic**: this folder is about data shape only. Verification belongs in `core/` and `adapters/`.
- **No DID exchange**: wallet or DIDComm choreography is out of scope here.
- **W3C publishes both contexts and JSON Schema**: we maintain both. Use JSON Schema for structural validation, JSON-LD context for linked-data processing.

## Upstream standards pinned

- W3C VC Data Model 2.0 — `vendor/w3c/vc-context-v2.jsonld`
- W3C Data Integrity 1.0 — `vendor/w3c/data-integrity-context.jsonld`
- W3C Bitstring Status List v1.0 — `vendor/w3c/bitstring-status-list-context.jsonld`
- W3C Controlled Identifiers — `vendor/w3c/controlled-identifiers-context.jsonld`

## Refreshing vendor artifacts

```bash
python schemas/tools/pin_upstream.py --family vc
```

## Running validation

```bash
python schemas/tools/validate.py --family vc
```
