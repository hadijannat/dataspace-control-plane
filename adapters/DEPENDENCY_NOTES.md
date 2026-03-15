# Adapters Dependency Notes

This file records cross-root follow-up that cannot be completed from `adapters/`
without violating the ownership map.

## Temporal Runtime Contract

- `core/procedure_runtime/ProcedureType` is narrower than the set of concrete
  workflows currently implemented in `procedures/`. The Temporal adapter now
  maps several workflow classes into the nearest available core category, but a
  richer `core` enum or a separate runtime workflow-kind contract would remove
  that lossy translation.
- `core/procedure_runtime/WorkflowGatewayPort` defines generic `approve`,
  `reject`, `pause`, `resume`, and `retry` controls, while many workflows in
  `procedures/` still expose procedure-specific Temporal update names such as
  `approve_case`, `pause_wallet`, or `accept_counteroffer`. The adapter now
  exposes the exact port surface, but end-to-end runtime convergence requires a
  shared control-name convention or explicit runtime metadata from the
  procedures owner.

## BaSyx Client Refresh

- The BaSyx wrapper now routes low-level request layout through checked-in
  generated-client modules inside `adapters/`. Refreshing those modules from
  live `/v3/api-docs` documents should be automated in a future repo-owned
  tooling step.

## Repo-Owned Follow-Up

- `tests/` owner: wire adapter-local contract tests into repo-wide compatibility
  and sandbox gates once the desired CI entrypoints are finalized.
- `docs/` owner: mirror the updated adapter boundary and health surfaces into
  architecture and runbook docs if those documents are intended to be public
  sources of truth.
