# apps — CLAUDE.md

## Purpose
Runtime surfaces: thin, compositional entrypoints that wire `core/`, `procedures/`, `adapters/`, `packs/`, and `schemas/` into user-facing and operator-facing products.

## Architecture Invariants
- **Thin entrypoints only.** `apps/` owns runtime wiring and UI rendering — not domain logic, canonical meaning, or integration protocol implementation.
- **Long-running mutations start Temporal workflows.** HTTP handlers must not do inline orchestration; they enqueue work via `procedures/`.
- **Browser code holds no machine-trust material.** `web-console` must not store machine private keys, long-lived operator secrets, or wallet signing material in client state.
- **`web-console` communicates only with `control-api`.** No direct adapter or database calls from the browser.
- **No domain logic in routers.** HTTP route handlers wire requests to procedure launches or adapter calls; they do not implement business rules.

## Build Order
1. Confirm `core/` contracts exist
2. `apps/control-api` (operator + public API)
3. `apps/temporal-workers` (workflow + activity registration)
4. `apps/edc-extension` (EDC runtime glue)
5. `apps/provisioning-agent` (declarative bootstrap reconciler)
6. `apps/web-console` (React operator console — last, depends on control-api contract)

## Forbidden Shortcuts
- Do not implement business rules in HTTP route handlers.
- Do not call adapters directly from `web-console` — route through `control-api`.
- Do not import from `infra/` — infra packaging is separate.

## Allowed Dependencies
- `core/` — canonical models and procedure contracts
- `procedures/` — workflow launch handles
- `adapters/` — infrastructure client implementations
- `packs/` — ecosystem overlays for UI feature flags
- `schemas/` — validation schemas for API request/response

## Verification
```bash
# App tests (once scaffolded)
make test-apps
pytest tests/integration -k apps
pytest tests/e2e -k web_console
pytest tests/tenancy -k operator_access
```

## Required Docs Updates
When `apps/` changes:
- Update `docs/api/` if control-api contract changes
- Update `docs/runbooks/` if operator workflows change
- Notify `infra-lead` if new environment variables, services, or ports are required

## Handoff Protocol
Write to `.claude/handoffs/apps.md` before going idle. Required fields:
- Runtime surfaces changed (which app subdirectory, what changed)
- API contract impact (new endpoints, changed request/response shapes)
- Workflow launch changes (new or modified procedure invocations)
- Generated-client impact (if control-api schema changed)
- Required downstream work (infra env vars, docs updates)
- Verification run outcome

## Full Guidebook
`docs/agents/apps-agent.md`
