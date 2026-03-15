# Core Dependency Notes

This refactor is intentionally `core/`-only. The following downstream owners need follow-up work to fully adopt the new public surface and remove deprecated shims.

## `adapters/`
- Stop importing `domains.*.model.*` directly and switch to each domain `api.py`.
- Update Postgres and IAM adapters to prefer tenant-scoped aggregate/repository contracts where available.
- Migrate audit imports from `audit.record` to `audit.api` / `audit.records`.
- Migrate procedure-runtime imports from `procedure_runtime.contracts` to `procedure_runtime.api`, `workflow_contracts.py`, and `messages.py`.

## `procedures/`
- Replace any free-form workflow payload assumptions with `procedure_runtime.workflow_contracts`.
- Move control messages to `procedure_runtime.messages`.
- Align search-attribute registration with `procedure_runtime.search_attributes`.

## `apps/temporal-workers`
- Bind worker/runtime registration to `procedure_runtime.temporal_bindings`.
- Update any direct task-queue or contract imports to the new `procedure_runtime.api`.

## `tests/`
- Restore `tests.fixtures` importability so `pytest tests/tenancy -k core -q` can run.
- Add repo-level tenancy and contract tests that exercise the new aggregate nouns and compatibility shims.

## `docs/`
- Update architecture docs to reflect `core/` as the installable semantic kernel.
- Document the new public import policy and one-cycle deprecation window for compatibility shims.
