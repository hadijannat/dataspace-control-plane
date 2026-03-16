# procedures — CLAUDE.md

## Purpose
Durable orchestration catalog: Temporal-based business workflows that coordinate `core/`, `adapters/`, and `packs/` to execute business intent without redefining canonical meaning.

## Architecture Invariants
- **One package per workflow family.** Each subdirectory owns one coherent business procedure (e.g., `procedures/company-onboarding/`).
- **Workflow code is deterministic and replay-safe.** Never call non-deterministic APIs (timestamps, UUIDs, random) directly in workflow code — use activities or deterministic SDK helpers.
- **Side effects belong exclusively in activities.** All I/O, external calls, and state mutations must be in activity functions, not workflow functions.
- **No raw secrets or large unstructured payloads in workflow state.** Use opaque references (vault paths, handle IDs) instead of inline credentials.

## Forbidden Shortcuts
- Do not redefine canonical types from `core/` — consume the procedure contracts from `core/procedure-runtime/`.
- Do not call adapter clients directly from workflow functions — always route through activities.
- Do not embed business rules that belong in `core/domains/` or `packs/`.

## Allowed Dependencies
- `core/` — procedure contracts, canonical models, audit primitives
- `packs/` — ecosystem overlays that affect workflow branching
- `docs/` — runbook context (read only)

## Verification
```bash
# Structural check
find procedures -maxdepth 2 -type d | sort

# Workflow and chaos tests (once scaffolded)
make test-procedures
pytest tests/integration -k procedures
pytest tests/unit -k replay
pytest tests/chaos -k workflows
```

## Required Docs Updates
When `procedures/` changes:
- Update `docs/runbooks/` for any operator-visible workflow state changes
- Update `docs/arc42/` if workflow family boundaries or evidence emission changes
- Notify `adapters-lead` if new activity signatures are needed

## Handoff Protocol
Write to `.claude/handoffs/procedures.md` before going idle. Required fields:
- Workflow identity changes (new workflow types, renamed phases)
- State or phase updates
- Activity changes (new, modified, or removed)
- Replay and versioning notes (anything that affects existing running workflows)
- Evidence emission changes
- Required adapter work (dependency notes for `adapters-lead`)
- Verification run outcome

## Full Guidebook
`docs/agents/procedures-agent.md`
