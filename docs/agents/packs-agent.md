# Packs Agent Guidebook

## Purpose
- Own `packs/` as the executable overlay layer for ecosystems, regulations, and enterprise-specific rule sets. Packs add versioned profile behavior and evidence requirements without becoming transport code or canonical meaning.

## Scope
- Define ecosystem and regulation overlays.
- Bind pack manifests to canonical domains, procedures, and schemas.
- Pin normative assets and provenance required for deterministic execution.
- Resolve cross-pack precedence and effective-date handling.

## Owned Paths
- `packs/catenax`
- `packs/manufacturing-x`
- `packs/gaia-x`
- `packs/espr-dpp`
- `packs/battery-passport`
- `packs/custom`

## Explicitly Non-Owned Paths
- `core/`
- `procedures/`
- `adapters/`
- `apps/`
- `schemas/`
- `tests/`
- `infra/`
- `docs/`

## What This Agent Must Read First
1. `packs/AGENTS.md`
2. `docs/agents/ownership-map.md`
3. `docs/agents/orchestration-guide.md`
4. `PLANS.md` for cross-pack or regulation-shaping work
5. Relevant `core/`, `schemas/`, and `docs/compliance-mappings/` materials

## Architecture Invariants
- Packs are overlays, not the semantic source of truth.
- Packs may add identifiers, evidence rules, policy constraints, delegated-act overlays, or profile-specific requirements.
- Transport code stays in `adapters/`.
- Canonical business meaning stays in `core/`.
- Runtime UI and API surfaces stay in `apps/`.
- Normative assets must be pinned locally. No network fetches at runtime for standards, profiles, or required contexts.

## Subdirectory-By-Subdirectory Responsibilities
### `packs/catenax`
- Pack kind: ecosystem
- Overlays: Catena-X membership, BPN-linked participation rules, cx-policy profile constraints, discovery and DTR expectations
- Adds: ecosystem identifiers, membership evidence, policy profile references, discoverability requirements
- Composition: often composes with `packs/espr-dpp` or `packs/battery-passport` for regulated publication
- Must remain in core instead: generic contract, policy, twin, and compliance semantics

### `packs/manufacturing-x`
- Pack kind: ecosystem
- Overlays: Manufacturing-X participation assumptions, data-sharing norms, operational digital-thread expectations
- Adds: ecosystem-scoped identifiers, pack-specific profile selections, required evidence for manufacturing collaboration
- Composition: may compose with `packs/catenax` where Tractus-X-derived infrastructure is reused
- Must remain in core instead: generic onboarding, contracts, and tenant topology semantics

### `packs/gaia-x`
- Pack kind: ecosystem
- Overlays: Gaia-X trust, compliance, federation metadata, and credential expectations
- Adds: Gaia-X profile references, trust proof requirements, compliance claims, federation-specific evidence
- Composition: may combine with regulatory packs when Gaia-X is the publication or compliance context
- Must remain in core instead: machine-trust semantics and compliance abstractions that are broader than Gaia-X

### `packs/espr-dpp`
- Pack kind: regulation
- Overlays: ESPR Digital Product Passport deadlines, role-based access tiers, and delegated-act-dependent requirements
- Adds: DPP obligation sets, product category requirement matrices, registry and identifier expectations, evidence gaps
- Composition: commonly layered with ecosystem packs that determine publication channel
- Must remain in core instead: generic compliance domain concepts and DPP lifecycle meaning

### `packs/battery-passport`
- Pack kind: regulation
- Overlays: Battery Regulation passport requirements, lifecycle metrics, PCF, durability, due diligence, and role-based access requirements
- Adds: battery-specific mandatory fields, evidence requirements, reporting timelines, and access control overlays
- Composition: often layered over `packs/espr-dpp` plus an ecosystem publication pack
- Must remain in core instead: generic DPP semantics, metering, and evidence envelopes

### `packs/custom`
- Pack kind: custom enterprise overlay
- Overlays: enterprise-specific governance, bilateral contract constraints, deployment-specific controls, or customer-only rules
- Adds: local identifiers, custom evidence rules, policy presets, compatibility exceptions approved by the operator
- Composition: may wrap any ecosystem or regulation pack, but must declare precedence explicitly
- Must remain in core instead: reusable business meaning that is not customer-specific

## Allowed Dependencies
- `core/` for canonical policy, contract, twin, trust, and compliance semantics
- `procedures/` for workflow touchpoints shaped by pack overlays
- `schemas/` for pinned pack manifests, examples, rule artifacts, and derived schema bundles
- `tests/` for pack validation and release gates
- `docs/` for compliance mapping, ADRs, and operator guidance

## Forbidden Shortcuts
- Do not put protocol transports, SDK calls, or runtime clients in packs.
- Do not hardcode pack-specific semantics into `core/` to avoid manifesting them in packs.
- Do not fetch normative assets from the network at runtime.
- Do not allow two packs to conflict silently; declare precedence or incompatibility.
- Do not store effective-date logic only in docs; encode it in pack manifests or metadata.

## Build / Implementation Order
1. Define or update the pack manifest and version.
2. Pin normative assets and provenance references.
3. Define identifiers, policies, evidence requirements, and effective-date metadata.
4. Bind pack overlays to canonical domains, procedures, and schemas.
5. Define pack composition and precedence rules.
6. Add positive and negative validation examples plus compatibility checks.
7. Update compliance and operator docs.

## Required Tests / Verification
- Existing structural checks:
  - `find packs -maxdepth 2 -type d | sort`
  - `test -f packs/AGENTS.md`
  - `test -f docs/agents/packs-agent.md`
- Expected command once scaffolded: `make test-packs`
- Expected command once scaffolded: `pytest tests/integration -k packs`
- Expected command once scaffolded: `pytest tests/compatibility -k packs`
- Expected command once scaffolded: `pytest tests/unit -k compliance`

## Required Docs Updates
- Update `docs/compliance-mappings/` whenever a pack adds or changes a regulatory or ecosystem requirement.
- Update `docs/arc42/` when pack layering or precedence changes architecture assumptions.
- Update `docs/runbooks/` when operator workflows for pack selection or evidence handling change.
- Update `docs/agents/packs-agent.md` and `packs/AGENTS.md` when pack boundaries or composition rules change.

## Common Failure Modes
- Pack rules silently duplicate or contradict `core/` semantics.
- Effective dates are not encoded and operators cannot tell which rules apply.
- Normative assets are referenced remotely and become unstable.
- Regulatory overlays are treated as UI hints instead of executable constraints.
- Custom packs bypass provenance and become impossible to audit.

## Handoff Contract
- Report pack versions changed, effective dates, provenance updates, and composition rules.
- Identify affected procedures, schemas, or adapters.
- State which normative assets were pinned or revised.
- Report verification run and docs updated.
- Leave dependency notes for any core or procedure work the pack now requires.

## Done Criteria
- Pack manifests are explicit, versioned, and provenance-aware.
- Core meaning remains separate from pack overlays.
- Conflicts and precedence are declared.
- No runtime network dependency exists for normative assets.
- Required compliance and operator docs are updated.

## Example Prompts For This Agent
- "Add an ESPR delegated-act overlay to `packs/espr-dpp` and document the evidence delta it requires."
- "Define how `packs/battery-passport` composes with `packs/catenax` for regulated asset publication."
- "Create a custom enterprise overlay in `packs/custom` for bilateral contract evidence without moving semantics into `core/`."
