---
title: "Adopt Temporal as the workflow engine for all durable business processes"
status: accepted
date: 2026-03-14
decision-makers:
  - procedures-lead
  - apps-lead
  - infra-lead
consulted:
  - core-lead
  - tests-lead
  - all-leads
informed:
  - all-leads
---

# Adopt Temporal as the workflow engine for all durable business processes

## Context and Problem Statement

The platform implements multi-step business processes that interact with multiple external systems: company onboarding touches Keycloak, Vault, Postgres, and an external DID registry; contract negotiation spans DSP protocol exchanges, DCP credential presentation, ODRL policy evaluation, and Postgres persistence; DPP export coordinates BaSyx AAS serialization, EU DPP registry submission, Vault signing, and metering event publication.

Each of these processes has partial failure modes: any step can fail independently, and re-running the entire process from the beginning is unacceptable for both idempotency reasons (Keycloak realm already exists) and operator experience reasons (a 10-step process that fails at step 9 must not restart at step 1). Classical approaches to this problem include:

1. **Custom outbox pattern**: Write-ahead log in Postgres, a background poller executes pending tasks. Requires building retry, backoff, dead-letter, and saga logic from scratch.
2. **Celery + Redis/Kombu**: Task queue with retry support but no replay-safe history, no time-skipping test support, and no determinism guarantees.
3. **Workflow-as-code engines (Temporal, Conductor)**: Durable execution with replay-safe history, built-in retry/backoff, and support for long-running workflows.

The platform specifically requires the ability to test time-dependent workflows (certificate expiry, metering window close, ODRL time-bound policy validation) without real-time waiting in tests.

## Decision Drivers

* Durable execution: multi-step processes must survive pod restarts, Postgres restarts, and network partitions without losing progress or duplicating side effects
* Replay safety: workflow history must be replayable to reconstruct state; non-determinism must be detectable
* Time-skipping test support: time-sensitive workflows must be testable at unit speed without `asyncio.sleep` or `time.sleep`
* Python SDK availability: the SDK must be mature and actively maintained for Python 3.12
* Workflow code as the runbook: the sequence of activities in the workflow definition must be readable by an operator as the manual procedure
* Activity retries must be configurable per-activity with exponential backoff, jitter, and maximum attempts

## Considered Options

* Temporal (chosen)
* Netflix Conductor
* Custom outbox pattern (SQLAlchemy + Postgres + background worker)
* Celery + Redis with Kombu chord/chain

## Decision Outcome

**Chosen option: "Temporal"**, because it is the only option that satisfies all decision drivers simultaneously. `WorkflowEnvironment.start_time_skipping()` uniquely enables deterministic, unit-speed testing of time-sensitive workflows — no other evaluated option supports this. The Python SDK (`temporalio`) is mature and actively maintained by Temporal Technologies. Workflow code is readable as a sequence of named activity invocations, making it suitable as the runbook. See [arc42/04-solution-strategy.md](../arc42/04-solution-strategy.md) and [arc42/08-crosscutting-concepts.md](../arc42/08-crosscutting-concepts.md) for how this decision shapes the architecture.

### Positive Consequences

* No compensating transaction code in application code — Temporal handles retry, backoff, and saga coordination
* Replay test suite (`tests/integration/replay/`) provides a determinism gate for all workflow changes
* Time-skipping tests allow metering window, certificate expiry, and policy time-bound tests to run in milliseconds
* Temporal UI provides real-time workflow monitoring without custom tooling
* Workflow history is the audit trail for regulated operations

### Negative Consequences

* Operational complexity: Temporal Server requires its own PostgreSQL database and must be deployed, monitored, and upgraded separately
* Determinism constraints: workflow code cannot use `random`, `datetime.now()`, external state reads, or non-deterministic data structures. This requires training and code review discipline.
* Temporal SDK version management: the `temporalio` SDK version must be pinned and upgraded carefully; workflow history format changes may require migration
* Temporal namespace must be bootstrapped before any worker starts (see Risk R-03 in arc42/11)

### Confirmation

`tests/integration/replay/` suite must pass before any change to `procedures/` merges. The suite executes each workflow, captures the Temporal workflow history, and replays it via `WorkflowEnvironment` to verify determinism.

## Pros and Cons of the Options

### Temporal

Durable workflow orchestration engine with replay-safe history, time-skipping test support, and a mature Python SDK.

* Good, because `WorkflowEnvironment.start_time_skipping()` enables unit-speed time-sensitive tests
* Good, because workflow history is immutable and replayable — provides audit trail without separate logging
* Good, because activity retries are configurable with `RetryPolicy(maximum_attempts, initial_interval, backoff_coefficient, maximum_interval)`
* Good, because Python SDK is production-grade and actively maintained
* Bad, because requires Temporal Server deployment (additional operational surface)
* Bad, because determinism constraints require workflow code discipline and linting

### Netflix Conductor

Open-source workflow orchestration engine with a JSON-based workflow DSL.

* Good, because JSON DSL is accessible to non-developers for workflow definition
* Bad, because Python SDK is community-maintained, not production-grade
* Bad, because no time-skipping test support — time-sensitive tests require real-time clock
* Bad, because workflow definitions are JSON, not code — making workflow code the runbook is impossible

### Custom Outbox Pattern

Write-ahead log in Postgres with a background worker polling for pending tasks.

* Good, because no additional infrastructure — Postgres is already required
* Good, because simple to implement for 1-2 step processes
* Bad, because requires building retry, backoff, dead-letter, and saga logic from scratch
* Bad, because no replay-safe history — non-determinism cannot be detected
* Bad, because time-sensitive testing requires real-time or mock clock injection
* Bad, because does not scale to 10+ step workflows with parallel activities

### Celery + Redis

Distributed task queue with retry support and parallel task execution.

* Good, because Python-native and widely used in the Python ecosystem
* Good, because simple to set up for single-step tasks
* Bad, because no replay-safe history
* Bad, because no time-skipping test support
* Bad, because saga/compensating transaction logic must be built manually
* Bad, because Redis is an additional infrastructure dependency with weaker durability guarantees than Postgres
