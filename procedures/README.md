# dataspace-control-plane-procedures

Temporal workflow definitions for the dataspace control plane.

## Purpose

This package implements all durable business orchestration for the dataspace
control plane as Temporal workflows and activities. It covers company onboarding,
connector bootstrap, wallet bootstrap, contract negotiation, digital-twin
publication, credential rotation, compliance checks, and more.

## Install

Install `dataspace-control-plane-core` first, then:

```bash
pip install -e ../core
pip install -e .
```

## Architecture Rules

- **No direct HTTP, DB, or SDK calls inside workflow code.** All side effects
  (REST calls, database writes, external SDK invocations) must live in
  *activities*. Workflows only orchestrate activities and child workflows.

- **Workflow code must be deterministic.** Never use `random`, `datetime.now()`,
  `uuid.uuid4()`, direct file I/O, or any non-deterministic library call inside
  a `@workflow.defn` class. Use `workflow.now()` for timestamps and pass any
  required random values in as input.

- **Idempotent activities.** Every activity must be safe to retry and replay.
  Use the idempotency key helpers in `_shared/ids.py` when calling external APIs.

- **History size.** Long-running entity workflows must call `should_continue_as_new`
  from `_shared/continue_as_new.py` before the history event count reaches the
  Temporal limit. Carry forward `DedupeState` snapshots across Continue-As-New.

## Shared Primitives

See `src/dataspace_control_plane_procedures/_shared/` for:

- `task_queues.py` — canonical task queue name constants
- `search_attributes.py` — typed Temporal search attribute keys
- `activity_options.py` — retry policies and activity option presets
- `ids.py` — workflow ID builders and activity idempotency key helpers
- `manifests.py` — `ProcedureManifest` static metadata descriptor
- `manual_review.py` — in-workflow human-in-the-loop state machine
- `compensation.py` — append-only compensation log for rollback ordering
- `continue_as_new.py` — history threshold check and deduplication state
- `versioning.py` — deterministic patch ID registry for safe deploys
- `testing.py` — fake activity factories and call-recording helpers

## Verification Notes

- The `procedures/tests` harness registers the custom Temporal search
  attributes used by these workflows before starting the time-skipping test
  server. This keeps integration, replay, and scenario tests aligned with the
  worker bootstrap contract.
- Long-lived workflows that continue-as-new restore typed carry state from a
  stable `CarryEnvelope` payload and wait for `workflow.all_handlers_finished`
  before checkpointing.

## Dependency Notes

- `docs/` owner: update operator runbooks and architecture notes to call out
  replay-safe manual-review timestamps, typed search-attribute registration,
  and the carry-envelope continue-as-new contract used by long-lived
  procedures.
- `tests/` owner: consider lifting the new Temporal time-skipping/search-
  attribute setup and replay fixtures into shared repo-wide test utilities once
  other roots need the same coverage.
- `apps/temporal-workers` owner: keep worker bootstrap aligned with the
  procedure registry and search-attribute catalog so workers fail fast if a
  workflow or search-attribute registration drifts from the procedure package.
