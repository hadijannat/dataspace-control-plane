# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

`dataspace-control-plane` is a monorepo for a multi-ecosystem dataspace control plane. It separates concerns across 9 strictly-owned layers so that changes to one layer cannot silently redefine another.

## Layer Architecture

Each top-level directory is a distinct architectural layer with exclusive ownership:

| Directory | Layer Role |
|-----------|-----------|
| `core/` | Semantic kernel — defines meaning, domains, canonical models, invariants, audit primitives. Nothing else defines meaning. |
| `procedures/` | Durable orchestration — Temporal-based business workflows, state machines, evidence emission. No integration logic here. |
| `adapters/` | Integration — normalizes external protocols (EDC, DSP, DCP, Gaia-X, Basyx, enterprise, infra) to core ports. |
| `packs/` | Ecosystem/regulatory overlays — Catena-X, Gaia-X, manufacturing-x, ESPR-DPP, battery-passport rules. |
| `schemas/` | Machine-readable artifacts — JSON Schema, JSON-LD contexts, ODRL policies, VC definitions, examples. |
| `apps/` | Runtime surfaces — thin, compositional entrypoints: `control-api`, `temporal-workers`, `web-console`, `edc-extension`, `provisioning-agent`. |
| `tests/` | Repo-wide verification — unit, integration, e2e, compatibility (DSP/DCP TCKs), tenancy, crypto-boundaries, chaos. |
| `infra/` | Delivery substrate — Helm, Terraform, Docker, observability stack. |
| `docs/` | Governance — ADRs, arc42 architecture, API contracts, runbooks, threat models, compliance mappings. |

**Dependency flow**: `schemas/` and `docs/` feed `core/`; `core/` feeds `procedures/`, `adapters/`, `packs/`; those feed `apps/`; everything feeds `tests/` and `docs/`.

## Ownership Rules

- **One specialist per root**: Each top-level directory has exactly one owner. No two owners edit the same root in the same task unless the prompt explicitly authorizes it.
- **Stay inside your root**: Do not edit files outside the owned directory. If a cross-boundary change is needed, make the local change only and leave an explicit dependency note for the neighboring owner.
- **Read the guidebook first**: Before editing any top-level directory, read `docs/agents/<directory>-agent.md` for the deep architecture rules, subdirectory responsibilities, and handoff contracts for that layer.
- **Forbidden zones** are documented in `docs/agents/ownership-map.md` — each owner has an explicit list of directories they must not touch.

## Planning

Use `PLANS.md` format for:
- Multi-hour tasks
- Changes crossing more than one ownership boundary
- Changes to trust, tenancy, compliance, or audit boundaries
- Changes to workflow contracts between `procedures/` and `apps/temporal-workers`
- Changes to canonical models (ripple through adapters, procedures, tests, docs)

Required plan shape: Objective → Affected directories → Architecture constraints → File-level plan → Verification → Docs updates → Rollback/compatibility notes.

## Verification

Each directory has its own verification gate. Run the relevant suite before finishing work in that directory:

```
pytest tests/unit -k <target>
pytest tests/integration -k <target>
pytest tests/e2e -k <target>
pytest tests/compatibility/dsp-tck
pytest tests/compatibility/dcp-tck
pytest tests/tenancy -k <target>
pytest tests/crypto-boundaries
pytest tests/chaos
```

Per-directory make targets (once scaffolded): `make test-apps`, `make test-core`, `make test-procedures`, `make test-adapters`, `make test-packs`, `make test-schemas`, `make test-infra`, `make test-docs`.

Tests must use deterministic fixtures and replay-safe Temporal verification. Keep tests free of secrets, production keys, and private material.

## Key Reference Files

- `AGENTS.md` — short routing layer and working model
- `PLANS.md` — planning rules and required plan shape
- `docs/agents/index.md` — guidebook index
- `docs/agents/ownership-map.md` — boundary rules, forbidden zones, handoff contracts
- `docs/agents/orchestration-guide.md` — how to split cross-directory work across owners
- `.agents/skills/` — repo-local reusable agent workflows

## Agent Teams

The repo runs on a 4-wave build model with 3–5 specialist teammate agents per wave. Each teammate owns exactly one top-level directory and must not edit any other.

### Wave Model

| Wave | Name | Active Teammates | Purpose |
|------|------|-----------------|---------|
| 0 | foundation-planning | core-lead, schemas-lead, infra-lead, docs-lead | Establish semantic foundation, schema registry, infra substrate, governance docs |
| 1 | platform-foundation | core-lead, schemas-lead, adapters-lead, infra-lead | Full canonical models, schema families, adapter integrations, infra packaging |
| 2 | execution-layer | procedures-lead, apps-lead, tests-lead, adapters-lead | Durable workflows, runtime app surfaces, integration verification |
| 3 | overlays-hardening | packs-lead, tests-lead, docs-lead | Ecosystem overlays, release gate hardening, governance completion |

### Wave Skills

Invoke these with the Skill tool or `/skill-name`:

| Skill | Purpose |
|-------|---------|
| `/start-wave` | Identify wave, list teammates and tasks, enforce coordinator mode |
| `/review-wave` | Read all handoffs, summarize status, flag missing artifacts |
| `/request-handoff` | Generate pre-filled handoff template for a directory |
| `/integrate-wave` | Synthesize wave into PLANS.md, surface cross-dir dependencies |
| `/close-wave` | Verify all handoffs present, emit closure checklist |

### Handoff Artifact

Every teammate must write `.claude/handoffs/<dir>.md` before going idle or completing a task. The `TeammateIdle` and `TaskCompleted` hooks enforce this. Template and protocol: `.claude/handoffs/README.md`.

Required fields: scope completed, files changed, verification run, design/contract changes, downstream impact, blockers, recommended next tasks.

### Lead Coordinator Rule

One lead per session. While teammates are active, the lead:
- Monitors progress via `/review-wave`
- Routes cross-boundary dependency notes between owners
- Does **not** implement code or edit product directories
- Runs `/integrate-wave` after all teammates complete, then `/close-wave`

Sequence: **explore → plan → delegate → monitor → integrate → close**

### Settings and Configuration

- `.claude/settings.json` — committed, team-shared project settings (permissions + hooks)
- `.claude/team-ownership.yaml` — machine-readable ownership map, wave definitions
- `.claude/hooks/` — lifecycle enforcement scripts (session-start, protect-shared-files, stop, audit, task-gate, idle-gate)

### Subagents

`.claude/agents/` contains one subagent definition per directory role:

| Agent | Owned Root |
|-------|-----------|
| `core-lead.md` | `core/` |
| `schemas-lead.md` | `schemas/` |
| `adapters-lead.md` | `adapters/` |
| `procedures-lead.md` | `procedures/` |
| `apps-lead.md` | `apps/` |
| `packs-lead.md` | `packs/` |
| `tests-lead.md` | `tests/` |
| `infra-lead.md` | `infra/` |
| `docs-lead.md` | `docs/` |

Use the Agent tool with `subagent_type` pointing to the relevant agent file for single-session subagent work.

Each directory also has a `<dir>/CLAUDE.md` loaded on-demand with local invariants, forbidden shortcuts, allowed dependencies, verification commands, and handoff protocol.

## Cross-Cutting Invariants

- `core/` defines meaning; orchestration never leaks into `core/`, integration never leaks into `procedures/`, and overlays never bypass `core/` invariants.
- Verify tenancy boundaries, operator boundaries, and machine-trust boundaries on every change.
- Prefer additive, explicit changes over hidden rewrites across ownership lines.
- Update `docs/` whenever interfaces, architecture, procedures, or operator workflows change.
- Include rollback or compatibility notes for external protocols, packs, schemas, workflows, and infrastructure packaging.
