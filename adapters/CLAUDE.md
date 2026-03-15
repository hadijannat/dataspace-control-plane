# adapters — CLAUDE.md

## Purpose
Anti-corruption and integration layer: implements `core/` ports, isolates transports and vendor APIs, and maps external systems into canonical forms.

## Architecture Invariants
- **Implement `core/` ports only.** Do not define new domain abstractions or semantic types.
- **Wire models stay local.** External JSON shapes, vendor DTOs, and protocol-specific types must not leak upward into `procedures/`, `apps/`, or `core/`.
- **Typed error mapping is mandatory.** Translate all external errors to canonical error types from `core/` — never propagate raw protocol errors.
- **Secrets and tokens never leak upward.** Credentials are consumed and used within the adapter; they must not appear in return values, logs, or workflow state.

## Forbidden Shortcuts
- Do not import from `procedures/` or `apps/`.
- Do not define canonical domain types — use the ones from `core/`.
- Do not pass raw authentication tokens or secrets to callers — use typed result objects.

## Allowed Dependencies
- `core/` — ports to implement and canonical types to return
- `schemas/` — validation schemas for wire format checking
- `packs/` — pack-specific protocol variants (read only)

## Verification
```bash
# Structural check
find adapters -maxdepth 3 -type d | sort

# Integration and compatibility tests (once scaffolded)
make test-adapters
pytest tests/integration -k adapters
pytest tests/compatibility/dsp-tck
pytest tests/compatibility/dcp-tck
```

## Required Docs Updates
When `adapters/` changes:
- Update `docs/api/` if public protocol behavior or capability advertisement changes
- Update `docs/runbooks/` if operational error handling changes
- Notify `tests-lead` if compatibility suite needs updating

## Handoff Protocol
Write to `.claude/handoffs/adapters.md` before going idle. Required fields:
- Ports implemented (which `core/` interfaces are now backed)
- Wire-model impact (new or changed external shapes)
- Health and readiness contract changes
- Secret handling notes
- Protocol compatibility implications
- Verification run outcome

## Full Guidebook
`docs/agents/adapters-agent.md`
