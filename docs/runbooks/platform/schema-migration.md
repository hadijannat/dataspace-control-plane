---
title: "Schema Migration"
summary: "Procedure for classifying, versioning, and safely migrating JSON Schema 2020-12 changes with CI gates and downstream consumer notification."
owner: schemas-lead
last_reviewed: "2026-03-16"
severity: "P3"
affected_services:
  - schemas
  - adapters
  - packs
  - control-api
status: approved
---

## When to Run This Procedure

Any time a file in `schemas/*/source/` is modified — whether for a field addition, field removal, constraint change, or editorial update. Schema changes have downstream consumers in adapters, procedures, packs, and the API spec; all must be notified of breaking changes.

## Change Classification

Run `diff_schema.py` to classify the change before making it:

```bash
# Compare the current schema against the previous git tag
python3 schemas/tools/diff_schema.py \
  schemas/metering/source/business/usage-record.schema.json \
  --against-tag $(git describe --tags --abbrev=0)
```

**Output classification**:

| Classification | Meaning | Required action |
|---------------|---------|----------------|
| `additive` | New optional field, new enum value, relaxed constraint | No version bump required; update tests if new field affects validation |
| `compatible` | Editorial change only (description, examples, title) | No action beyond commit |
| `breaking` | Removed required field, narrowed type, removed enum value, changed field semantics | **Version bump required** — see Breaking Change Procedure below |

## Additive Change Procedure

For additive changes (new optional fields, new enum values):

```bash
# 1. Make the change to the source schema
# 2. Run the diff tool to confirm classification
python3 schemas/tools/diff_schema.py \
  schemas/metering/source/business/usage-record.schema.json \
  --against-tag $(git describe --tags --abbrev=0)
# Expected: "classification: additive"

# 3. Update the golden snapshot if the test compares to it
python3 -m pytest tests/unit/schemas/test_usage_record_schema.py -v

# 4. Run the full schema test suite
python3 -m pytest tests/unit/schemas/ tests/compatibility/ -v

# 5. Re-generate the bundled schema
redocly bundle schemas/metering/source/business/usage-record.schema.json \
  -o schemas/metering/bundles/usage-record.bundle.json

# 6. Commit
git add schemas/metering/source/business/usage-record.schema.json
git add schemas/metering/bundles/usage-record.bundle.json
git commit -m "schemas(metering): add optional bytesTransferred field to usage-record"
```

## Breaking Change Procedure

For breaking changes, additional steps are required to prevent silent consumer breakage:

### Step 1: Confirm the change is truly breaking

```bash
python3 schemas/tools/diff_schema.py \
  schemas/metering/source/business/usage-record.schema.json \
  --against-tag $(git describe --tags --abbrev=0)
# Expected: "classification: breaking" with details of the breaking change
```

### Step 2: Create a new versioned schema file

```bash
# Copy the current schema to a v2 file
cp schemas/metering/source/business/usage-record.schema.json \
   schemas/metering/source/business/usage-record.v2.schema.json

# Update the $id in the new file to reflect v2
# Edit: "$id": "https://schemas.dataspace.internal/metering/usage-record/v2"

# Keep the old schema file unchanged (for backward compatibility during deprecation window)
```

### Step 3: Update the registry if applicable

If `schemas/metering/registry.yaml` references the schema, add the new v2 entry alongside the v1 entry:

```yaml
# schemas/metering/registry.yaml
schemas:
  - id: "usage-record"
    version: "1.0.0"
    file: "source/business/usage-record.schema.json"
    status: deprecated
    deprecation_date: "2026-09-14"  # 6 months after v2 introduction
  - id: "usage-record"
    version: "2.0.0"
    file: "source/business/usage-record.v2.schema.json"
    status: active
```

### Step 4: Notify downstream consumers

Leave dependency notes in the following locations:

```bash
# 1. Update docs/arc42/11-risks-and-technical-debt.md with a new tech debt item
# 2. Leave a note in adapters/messaging/kafka/CLAUDE.md if kafka adapter uses this schema
# 3. Leave a note in packs/*/CLAUDE.md if any pack validates against this schema
# 4. Update docs/api/changelog.md if the API surface changes
```

### Step 5: Update tests to reference the new schema version

```bash
# Update golden snapshots for tests that validate against the changed schema
python3 -m pytest tests/unit/schemas/test_usage_record_schema.py --update-snapshots

# Run all schema tests to ensure v1 still passes and v2 also passes
python3 -m pytest tests/unit/schemas/ tests/compatibility/ -v
```

### Step 6: Update API changelog if API surface changed

If the breaking schema change affects an API request or response body:

```bash
# Update docs/api/changelog.md with the breaking change entry
# Update docs/api/openapi/source/control-api.yaml if schema references changed
# Re-run redocly lint
redocly lint docs/api/openapi/source/control-api.yaml
```

## CI Gate

The schema CI gate runs automatically on every PR that modifies files in `schemas/`:

```bash
# This runs in CI — you can run it locally to preview
make test-schemas
```

The CI gate:

1. Runs `diff_schema.py` against the base branch (not a tag) for all changed schema files
2. Fails if any change is classified as `breaking` without a corresponding new versioned file
3. Runs `test_schema_meta_compliance.py` to verify all local schemas declare `$schema: 2020-12`
4. Runs `test_provenance_present.py` to verify all vendor files have `provenance.json`
5. Runs `redocly lint` on the OpenAPI spec if it was modified

## Startup Readiness Gate

The hardened control-api startup path now checks both required tables and the
applied migration level before it marks the database dependency healthy.

Required tables for procedure start/status behavior:

- `audit_records`
- `http_idempotency_keys`
- `procedures`
- `schema_migrations`

Required migration level: `3`

Quick check:

```sql
SELECT version, description, applied_at
FROM schema_migrations
ORDER BY version;
```

Expected rows include:

- `1 | initial_schema`
- `2 | procedure_runtime_tables`
- `3 | schema_migrations`

If the latest version is missing, the control-api starts in degraded mode and
procedure routes that need Postgres-backed durability return `503` until the
migration is applied.

## Evidence Capture

- [ ] `diff_schema.py` output (additive / breaking classification)
- [ ] If breaking: new versioned file path and updated registry.yaml
- [ ] Test suite output (`make test-schemas`)
- [ ] List of downstream consumers notified
- [ ] `schema_migrations` shows the expected latest version after rollout

## Related Runbooks

- [DPP Export Stuck](../procedures/dpp-export-stuck.md) — if a schema change caused a pack validation failure that blocked an export
