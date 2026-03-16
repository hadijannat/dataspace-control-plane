# dataspace-control-plane

A monorepo for a multi-ecosystem dataspace control plane. Implements the
[Eclipse Dataspace Protocol (DSP)](https://docs.internationaldataspaces.org/ids-knowledgebase/dataspace-protocol),
[Dataspace Connect Protocol (DCP)](https://docs.internationaldataspaces.org/ids-knowledgebase/v/dataspace-connect-protocol),
and ecosystem overlays (Catena-X, Gaia-X, Manufacturing-X, ESPR-DPP, Battery Passport) on a
Temporal-based durable workflow engine.

---

## Architecture

Nine strictly-owned layers. Each layer has exactly one owner; no layer borrows logic from a
layer it feeds.

| Directory | Layer | Role |
|-----------|-------|------|
| `core/` | Semantic kernel | Canonical domain models, invariants, procedure contracts, audit primitives |
| `procedures/` | Durable orchestration | Temporal workflows and activities; state machines; evidence emission |
| `adapters/` | Integration | Protocol normalizers: EDC, DSP, DCP, Gaia-X, BaSyX, Kafka, Vault, Postgres |
| `packs/` | Ecosystem overlays | Catena-X, Gaia-X, Manufacturing-X, ESPR-DPP, Battery Passport rule sets |
| `schemas/` | Artifact registry | Pinned upstream standards (AAS, ODRL, W3C VC) + authored JSON Schema 2020-12 families |
| `apps/` | Runtime surfaces | `control-api`, `temporal-workers`, `web-console`, `edc-extension`, `provisioning-agent` |
| `tests/` | Verification spine | Unit, integration, e2e, DSP/DCP TCKs, tenancy, crypto-boundaries, chaos |
| `infra/` | Delivery substrate | Helm charts, Terraform modules, Docker images, observability stack |
| `docs/` | Governance | arc42 architecture, ADRs, API contracts, runbooks, threat model, compliance mappings |

**Dependency flow:** `schemas/` and `docs/` feed `core/`; `core/` feeds `procedures/`,
`adapters/`, and `packs/`; those feed `apps/`; everything feeds `tests/` and `docs/`.

---

## Prerequisites

| Tool | Minimum version | Used for |
|------|-----------------|----------|
| Python | 3.12 | All Python packages |
| [uv](https://github.com/astral-sh/uv) | 0.4+ | Python dependency management |
| Node.js | 20 | `apps/web-console` (Vite 6 / React 19) |
| [pnpm](https://pnpm.io) | 9 | web-console package manager |
| Java | 21 | `apps/edc-extension` (Gradle Kotlin DSL) |
| [Helm](https://helm.sh) | 3.14+ | `infra/helm` chart validation |
| [Terraform](https://terraform.io) | 1.7+ | `infra/terraform` environment validation |
| Docker | 24+ | Local compose environments |
| [go-task](https://taskfile.dev) | 3+ | Optional — mirrors `make` targets as `task` commands |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-org/dataspace-control-plane.git
cd dataspace-control-plane

# 2. Install all dependencies
make install

# 3. Run unit tests (no live services required)
make test
```

---

## Testing

### Per-directory targets

Each target exercises one ownership layer. None of these require live services.

```bash
make test-core        # core/ semantic layer — unit + tenancy
make test-schemas     # schemas/ artifact layer — unit + offline schema validation
make test-procedures  # procedures/ orchestration — unit + replay tests
make test-adapters    # adapters/ integration — pure-Python adapter contracts
make test-packs       # packs/ overlays — unit + integration
make test-apps        # apps/ runtime surfaces — integration + e2e
make test-infra       # infra/ substrate — helm lint + terraform validate
make test-docs        # docs/ explanation layer — markdownlint + link check
```

### Release gate suites

These suites guard wave closure. They require a running local environment with
Temporal, Postgres, Vault, and Kafka (see `infra/compose/`).

```bash
make test-gates       # DSP TCK + DCP TCK + tenancy + crypto-boundaries

# Individual gate suites (with --live-services)
pytest tests/compatibility/dsp-tck --live-services
pytest tests/compatibility/dcp-tck --live-services
pytest tests/tenancy --live-services
pytest tests/crypto-boundaries --live-services
```

### Chaos tests

```bash
make test-chaos       # fault-injection environment required
```

### Full unit suite

```bash
make test             # equivalent to: pytest -m "not (integration or chaos or tenancy or crypto)"
```

---

## Linting

```bash
make lint             # all linters: ruff + ESLint + markdownlint + helm lint
make lint-python      # ruff check across all Python packages
make lint-node        # ESLint for web-console
make lint-docs        # markdownlint for docs/
make lint-infra       # helm lint for infra/helm/
```

---

## Documentation Site

Architecture docs (arc42, ADRs, API contracts, runbooks, threat model) are built with
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

```bash
make docs-serve       # live preview at http://127.0.0.1:8000
make docs-build       # build to site/ (strict mode)
make test-docs        # markdownlint-cli2 + docs pytest + Redocly + MkDocs strict build
```

The docs toolchain is split by runtime:

- `docs/requirements.txt` provisions MkDocs, Material, Mermaid-capable Markdown extensions, and the strict site build plugins.
- `docs/package.json` provisions repo-local docs linters and OpenAPI tooling (`markdownlint-cli2`, `@redocly/cli`).

Only source Markdown/YAML is versioned. `site/` stays out of version control, and rendered
OpenAPI HTML is generated in CI only.

---

## go-task Equivalents

If you prefer [go-task](https://taskfile.dev) over Make:

```bash
task install          # install all dependencies
task test             # run unit tests
task test:gates       # run release gate suites
task lint             # run all linters
task docs:serve       # serve docs site
task clean            # remove build artifacts
```

All targets are mirrored in `Taskfile.yml`.

---

## Agent / AI Tooling

This repo is designed for Claude Code agent-teams. See `CLAUDE.md` for the full model.

| Resource | Purpose |
|----------|---------|
| `AGENTS.md` | Short routing guide and working model |
| `PLANS.md` | Planning rules and required plan shape |
| `CLAUDE.md` | Claude Code project settings and agent-team model |
| `docs/agents/index.md` | Guidebook index (one per directory) |
| `docs/agents/ownership-map.md` | Boundary rules, forbidden zones, handoff contracts |
| `docs/agents/orchestration-guide.md` | How to split cross-directory work across owners |
| `.claude/agents/` | Subagent definitions (one per directory role) |
| `.claude/skills/` | Wave management skills (`/start-wave`, `/review-wave`, etc.) |
| `.agents/skills/` | Repo-local reusable agent workflows |
| `.claude/handoffs/` | Inter-wave handoff artifacts (one per directory) |

### Wave model

The repo runs on a 4-wave build model. Each wave activates 3–5 specialist teammate agents:

| Wave | Name | Active teammates |
|------|------|-----------------|
| 0 | foundation-planning | core-lead, schemas-lead, infra-lead, docs-lead |
| 1 | platform-foundation | core-lead, schemas-lead, adapters-lead, infra-lead |
| 2 | execution-layer | procedures-lead, apps-lead, tests-lead, adapters-lead |
| 3 | overlays-hardening | packs-lead, tests-lead, docs-lead |

---

## Key Reference Files

- [`AGENTS.md`](AGENTS.md) — routing and working model
- [`PLANS.md`](PLANS.md) — planning rules
- [`CODEOWNERS`](CODEOWNERS) — GitHub ownership assignments
- [`docs/agents/ownership-map.md`](docs/agents/ownership-map.md) — boundary rules
- [`docs/agents/orchestration-guide.md`](docs/agents/orchestration-guide.md) — cross-directory orchestration

---

## Contributing

1. Read `AGENTS.md` and `docs/agents/ownership-map.md` before making changes.
2. Each PR must stay within one ownership boundary. Cross-boundary changes require a plan (`PLANS.md` format).
3. Run `make test` (and the relevant `make test-<dir>` target) before submitting.
4. Release gate suites (`make test-gates`) must pass before any wave closes.
5. Write a handoff artifact (`.claude/handoffs/<dir>.md`) for significant changes.
