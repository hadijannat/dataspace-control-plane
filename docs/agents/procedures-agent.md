# Procedures Agent Guidebook

## Purpose
- Own `procedures/` as the durable orchestration catalog. Procedures coordinate `core/`, `adapters/`, and `packs/` to execute business workflows without redefining canonical meaning.

## Scope
- Implement one business procedure package per workflow family.
- Encode state progression, approval points, evidence emission, and child workflow boundaries.
- Coordinate adapters through activities or equivalent side-effect boundaries.
- Preserve replay safety, versioning discipline, and explicit operator review steps.

## Owned Paths
- `procedures/company-onboarding`
- `procedures/connector-bootstrap`
- `procedures/wallet-bootstrap`
- `procedures/publish-asset`
- `procedures/register-digital-twin`
- `procedures/negotiate-contract`
- `procedures/dpp-provision`
- `procedures/evidence-export`
- `procedures/delegate-tenant`
- `procedures/rotate-credentials`
- `procedures/revoke-credentials`

## Explicitly Non-Owned Paths
- `core/`
- `adapters/`
- `apps/`
- `packs/`
- `schemas/`
- `tests/`
- `infra/`
- `docs/`

## What This Agent Must Read First
1. `procedures/AGENTS.md`
2. `docs/agents/ownership-map.md`
3. `docs/agents/orchestration-guide.md`
4. `PLANS.md` for any workflow family addition or cross-owner change
5. Relevant domain contracts in `core/` and pack overlays in `packs/`

## Architecture Invariants
- `procedures/` coordinates existing meaning from `core/`; it does not redefine it.
- One package maps to one workflow family. Avoid catch-all orchestration packages.
- Workflow code must be deterministic.
- Side effects, network IO, secret retrieval, and clock-sensitive behavior must stay in activities or equivalent external calls.
- Activities must be idempotent or compensatable.
- Signals, updates, and queries must have stable contracts and validation boundaries.
- Long-lived workflows must define continue-as-new rules.
- Procedure state must never contain raw secrets, private keys, mutable adapter clients, or unbounded payloads.

## Subdirectory-By-Subdirectory Responsibilities
### `procedures/company-onboarding`
- Purpose: onboard a company or tenant into the control plane and establish initial control-plane readiness.
- Workflow key: `procedure.company_onboarding.v1`
- Key phases and states: intake, eligibility review, topology seed, operator bootstrap, connector and wallet fan-out, readiness confirmation, evidence finalization.
- Likely activities: validate intake data, reserve tenant identifiers, request operator IAM provisioning, start bootstrap child workflows, persist onboarding evidence.
- Common manual-review points: legal entity validation, policy acceptance, exception approvals for incomplete trust material.
- Likely child workflow boundaries: `connector-bootstrap`, `wallet-bootstrap`, possibly `delegate-tenant`.
- Likely packs involved: `packs/catenax`, `packs/manufacturing-x`, `packs/gaia-x`, `packs/custom`.
- Likely evidence emitted: onboarding packet, approval trail, trust-bootstrap references, initial compliance checklist.

### `procedures/connector-bootstrap`
- Purpose: bootstrap dataspace connector participation for a tenant or environment.
- Workflow key: `procedure.connector_bootstrap.v1`
- Key phases and states: desired-state intake, infrastructure readiness, connector provisioning, registration, health verification, handoff.
- Likely activities: call provisioning agent or infra hooks, configure connector runtime, register catalogs or endpoints, verify readiness.
- Common manual-review points: network zone exceptions, external DNS or certificate approvals.
- Likely child workflow boundaries: none by default; may call `rotate-credentials` if initial materials are stale.
- Likely packs involved: ecosystem packs plus `packs/custom`.
- Likely evidence emitted: connector registration record, readiness report, environment inventory.

### `procedures/wallet-bootstrap`
- Purpose: establish wallet, DID, credential, and trust-material readiness for machine actors.
- Workflow key: `procedure.wallet_bootstrap.v1`
- Key phases and states: trust requirements intake, DID setup, key material binding, credential issuance or import, verification, evidence closure.
- Likely activities: request vault handles, call wallet or identity adapters, validate credential chains.
- Common manual-review points: external issuer approval, trust root exceptions, imported credential validation failures.
- Likely child workflow boundaries: `rotate-credentials` when imported or seeded materials must be rotated immediately.
- Likely packs involved: `packs/catenax`, `packs/gaia-x`, `packs/custom`.
- Likely evidence emitted: DID references, issuance logs, credential inventory, trust verification results.

### `procedures/publish-asset`
- Purpose: publish enterprise data as a governed dataspace asset.
- Workflow key: `procedure.publish_asset.v1`
- Key phases and states: source selection, schema mapping, policy composition, connector publication, catalog verification, evidence closure.
- Likely activities: inspect enterprise source, validate mappings, materialize asset metadata, push publication to EDC adapters, verify discoverability.
- Common manual-review points: data classification review, policy exceptions, public metadata approval.
- Likely child workflow boundaries: `register-digital-twin` if asset publication must align with twin registration.
- Likely packs involved: ecosystem packs, `packs/espr-dpp`, `packs/battery-passport`.
- Likely evidence emitted: asset manifest, policy record, publication confirmation, lineage snapshot.

### `procedures/register-digital-twin`
- Purpose: register digital twin or AAS-linked resources in dataspace-facing systems.
- Workflow key: `procedure.register_digital_twin.v1`
- Key phases and states: twin intake, canonical mapping, AAS registration, connector linkage, visibility verification, evidence closure.
- Likely activities: map canonical twin records to AAS submodels, call BaSyx or registry adapters, establish EDC references, validate discoverability.
- Common manual-review points: incomplete submodel coverage, pack-specific identifier conflicts, namespace approval.
- Likely child workflow boundaries: `publish-asset` for associated data assets or `dpp-provision` for regulated twin packages.
- Likely packs involved: `packs/catenax`, `packs/manufacturing-x`, `packs/espr-dpp`, `packs/battery-passport`.
- Likely evidence emitted: twin registration record, AAS descriptor references, link integrity report.

### `procedures/negotiate-contract`
- Purpose: execute governed contract negotiation across supported dataspace profiles.
- Workflow key: `procedure.negotiate_contract.v1`
- Key phases and states: offer selection, policy preparation, negotiation exchange, agreement review, acceptance, evidence closure.
- Likely activities: map canonical contract intent to protocol-specific terms, drive negotiation via EDC or DSP adapters, persist agreement references.
- Common manual-review points: legal override, unusual obligations, cross-pack policy conflicts, counterparty trust exceptions.
- Likely child workflow boundaries: `publish-asset` for provider-side prerequisites or `evidence-export` for compliance packet generation.
- Likely packs involved: ecosystem packs and regulatory packs affecting permitted terms.
- Likely evidence emitted: negotiation transcript references, agreement evidence, obligation summary.

### `procedures/dpp-provision`
- Purpose: provision and maintain Digital Product Passport readiness for regulated product sets.
- Workflow key: `procedure.dpp_provision.v1`
- Key phases and states: regulation selection, product scoping, schema binding, evidence gap analysis, publication readiness, submission or exposure.
- Likely activities: compute pack overlays, validate required submodels, aggregate source data, prepare DPP artifacts, request publication.
- Common manual-review points: regulatory gap overrides, delegated-act interpretation, missing lifecycle data, PCF exceptions.
- Likely child workflow boundaries: `register-digital-twin`, `publish-asset`, `evidence-export`.
- Likely packs involved: `packs/espr-dpp`, `packs/battery-passport`, ecosystem packs where publication target matters.
- Likely evidence emitted: compliance matrix, DPP artifact references, gap report, readiness decision trail.

### `procedures/evidence-export`
- Purpose: export audit, compliance, onboarding, negotiation, or DPP evidence for operators or auditors.
- Workflow key: `procedure.evidence_export.v1`
- Key phases and states: request intake, evidence scope resolution, material collection, redaction or filtering, export packaging, delivery confirmation.
- Likely activities: query audit references, fetch evidence bundles, apply policy-aware filtering, create export manifests, persist delivery records.
- Common manual-review points: redaction approval, regulator-specific packaging, legal hold checks.
- Likely child workflow boundaries: none by default; may run as a child of other procedures for structured evidence output.
- Likely packs involved: regulatory and ecosystem packs affecting required evidence.
- Likely evidence emitted: export manifest, delivery receipt, redaction log.

### `procedures/delegate-tenant`
- Purpose: delegate tenant or subtenant administration with explicit topology and operator-access controls.
- Workflow key: `procedure.delegate_tenant.v1`
- Key phases and states: delegation request, topology validation, access rule check, assignment, confirmation, audit closure.
- Likely activities: validate tenant lineage, apply operator access rules, configure target assignments, persist audit evidence.
- Common manual-review points: separation-of-duty exceptions, delegated admin scope approval.
- Likely child workflow boundaries: `wallet-bootstrap` if delegated tenants need dedicated trust material.
- Likely packs involved: `packs/custom` and any ecosystem pack with membership-specific delegation rules.
- Likely evidence emitted: delegation record, access decision evidence, topology update trace.

### `procedures/rotate-credentials`
- Purpose: rotate trust materials, connector secrets, or delegated credentials without losing procedural traceability.
- Workflow key: `procedure.rotate_credentials.v1`
- Key phases and states: rotation request, impact analysis, staged issuance, cutover, verification, retirement evidence.
- Likely activities: mint or import replacements, update references, test validity, revoke superseded materials, notify dependents.
- Common manual-review points: emergency rotations, dual-control approval, external issuer delays.
- Likely child workflow boundaries: none; often invoked by other procedures as a remediation path.
- Likely packs involved: ecosystem packs with credential profile rules plus `packs/custom`.
- Likely evidence emitted: rotation manifest, validity checks, revocation references, incident linkage when applicable.

### `procedures/revoke-credentials`
- Purpose: revoke compromised or obsolete trust materials and capture required evidence.
- Workflow key: `procedure.revoke_credentials.v1`
- Key phases and states: revocation request, impact assessment, revoke execution, downstream containment, evidence closure.
- Likely activities: call issuer or wallet adapters, propagate revocation status, quarantine affected workflows, notify operators.
- Common manual-review points: emergency compromise handling, legal hold, coordinated partner communication.
- Likely child workflow boundaries: `rotate-credentials` if replacement is coupled to revocation.
- Likely packs involved: ecosystem-specific trust profiles and compliance packs when regulatory reporting is required.
- Likely evidence emitted: revocation record, impact report, containment log, notification evidence.

## Allowed Dependencies
- `core/` for canonical inputs, state contracts, audit semantics, and business rules
- `adapters/` for side effects and external-system interactions through activities
- `packs/` for ecosystem or regulation overlays that shape workflow paths
- `tests/` for integration, replay, tenancy, and chaos coverage
- `docs/` for runbooks, procedure references, and reviewer guidance

## Forbidden Shortcuts
- Do not embed vendor SDK calls directly in deterministic workflow code.
- Do not persist secrets, raw payload dumps, or unbounded catalogs inside workflow state.
- Do not turn pack-specific rules into invisible branches with no recorded evidence.
- Do not let signals or updates mutate state without validation and audit relevance.
- Do not skip versioning notes when a workflow identity, input shape, or state progression changes.

## Build / Implementation Order
1. Confirm canonical contracts and pack overlays required by the procedure.
2. Define workflow identity, input, state, and evidence outputs.
3. Define activity boundaries and idempotency expectations.
4. Add signal, update, and query contracts only after the base state machine is clear.
5. Add child workflow boundaries for reusable long-running subprocesses.
6. Add replay, versioning, and continue-as-new rules before shipping.
7. Add integration, replay, tenancy, and evidence-export verification.

## Required Tests / Verification
- Existing structural checks:
  - `find procedures -maxdepth 2 -type d | sort`
  - `test -f procedures/AGENTS.md`
  - `test -f docs/agents/procedures-agent.md`
- Expected command once scaffolded: `make test-procedures`
- Expected command once scaffolded: `pytest tests/integration -k procedures`
- Expected command once scaffolded: `pytest tests/unit -k replay`
- Expected command once scaffolded: `pytest tests/chaos -k workflows`

## Required Docs Updates
- Update `docs/runbooks/` for operator-facing workflow or remediation changes.
- Update `docs/arc42/` when orchestration topology or workflow ownership changes.
- Update `docs/compliance-mappings/` when evidence or regulatory flows change.
- Update `docs/agents/procedures-agent.md` and `procedures/AGENTS.md` when package boundaries or procedure identities change.

## Common Failure Modes
- Workflow code performs network IO or randomization directly.
- Large mutable payloads are stored in workflow state and break replay or scale assumptions.
- Manual review points are buried inside generic error handling.
- Child workflow boundaries are chosen too late, producing monolith workflows.
- Signals and updates are added without stable contracts or authorization rules.
- Pack-driven branching is undocumented and impossible to audit.

## Handoff Contract
- Report affected procedure packages and workflow keys.
- Report changed states, activities, signals, updates, queries, and child workflow boundaries.
- List packs involved and evidence emitted.
- State replay, versioning, continue-as-new, or migration concerns.
- Record required follow-up in `core/`, `adapters/`, `apps/temporal-workers`, `tests/`, or `docs/`.

## Done Criteria
- Each package remains one workflow family.
- Workflow semantics come from `core/` and overlays from `packs/`, not ad hoc local meaning.
- Determinism, idempotency, replay, and continue-as-new expectations are documented.
- Manual review points and evidence outputs are explicit.
- Dependency notes exist for any missing upstream or downstream capability.

## Example Prompts For This Agent
- "Add a new review state to `procedures/negotiate-contract` for legal override and document the evidence emitted."
- "Define the workflow identity and child workflow boundaries for `procedures/dpp-provision` using pack-specific compliance overlays."
- "Update `procedures/rotate-credentials` to support staged cutover while preserving replay safety and handoff notes."
