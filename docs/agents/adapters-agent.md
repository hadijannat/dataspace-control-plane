# Adapters Agent Guidebook

## Purpose
- Own `adapters/` as the anti-corruption and integration layer. Adapters implement `core/` ports, isolate transports and vendor APIs, and map external systems into canonical forms.

## Scope
- Implement dataspace protocol and ecosystem integrations.
- Implement enterprise source-system connectors.
- Implement infrastructure-facing clients for IAM, KMS, persistence, workflow runtime, and telemetry.
- Keep wire formats local and expose canonical models or typed port results upward.

## Owned Paths
- `adapters/dataspace/edc`
- `adapters/dataspace/dsp`
- `adapters/dataspace/dcp`
- `adapters/dataspace/tractusx`
- `adapters/dataspace/gaiax`
- `adapters/dataspace/basyx`
- `adapters/enterprise/sap-odata`
- `adapters/enterprise/siemens-teamcenter`
- `adapters/enterprise/kafka-ingest`
- `adapters/enterprise/object-storage`
- `adapters/enterprise/sql-extract`
- `adapters/infrastructure/keycloak`
- `adapters/infrastructure/vault-kms`
- `adapters/infrastructure/temporal-client`
- `adapters/infrastructure/postgres`
- `adapters/infrastructure/telemetry`

## Explicitly Non-Owned Paths
- `core/`
- `procedures/`
- `apps/`
- `packs/`
- `schemas/`
- `tests/`
- `infra/`
- `docs/`

## What This Agent Must Read First
1. `adapters/AGENTS.md`
2. `docs/agents/ownership-map.md`
3. `docs/agents/orchestration-guide.md`
4. `PLANS.md` for protocol, trust, or compatibility changes
5. Relevant core ports and schema artifacts before implementing any adapter

## Architecture Invariants
- Adapters implement ports defined by `core/`; they do not redefine canonical meaning.
- Transport clients, external DTOs, JSON-LD profiles, vendor SDK types, and protocol quirks stay inside adapter packages.
- Errors must be mapped from external systems into explicit typed outcomes that upstream layers can reason about.
- Secret retrieval, token exchange, and credential material are infrastructure concerns within adapters; secrets never leak upward.
- Composition adapters may assemble multiple leaf adapters, but they still return canonical or explicitly typed composition results.

## Subdirectory-By-Subdirectory Responsibilities
### `adapters/dataspace/edc`
- Ports to implement: asset publication, catalog discovery, contract negotiation, transfer management, policy submission, connector management.
- Local wire models: EDC management API payloads, connector configuration documents, protocol-specific metadata.
- Canonical mapping: map assets, offers, agreements, obligations, transfer statuses, and policy references into `core/domains/contracts`, `core/domains/policies`, and `core/domains/schema-mapping`.
- Health and readiness: verify control-plane reachability, expected extension compatibility, connector registration state, and policy engine readiness.
- Must never leak into core: EDC DTOs, extension wiring details, raw management API error payloads.

### `adapters/dataspace/dsp`
- Ports to implement: DSP request/response exchange, negotiation transport, agreement retrieval, transfer control, catalog consumption.
- Local wire models: DSP JSON-LD messages, profile-specific envelopes, HTTP-level transport headers.
- Canonical mapping: translate DSP negotiation and transfer artifacts into canonical contract and transfer state.
- Health and readiness: validate protocol profile compatibility, endpoint reachability, and JSON-LD context pinning.
- Must never leak into core: raw DSP envelopes, profile-specific terms, transport retry heuristics.

### `adapters/dataspace/dcp`
- Ports to implement: DCP-specific participation or control-plane interactions once the protocol surface is defined.
- Local wire models: DCP request and response documents, capability descriptions, profile metadata.
- Canonical mapping: normalize DCP-specific control surfaces into canonical tenant, contract, and compliance views.
- Health and readiness: verify capability negotiation and protocol-version compatibility.
- Must never leak into core: DCP wire-level capability documents or protocol negotiation quirks.

### `adapters/dataspace/tractusx`
- Ports to implement: Tractus-X-specific composition over EDC, DTR, identity, and profile requirements.
- Local wire models: Tractus-X profile documents, BPN- and identity-specific payloads, profile-specific policy vocabulary.
- Canonical mapping: map profile-specific identifiers, discovery results, and membership checks into canonical topology, contract, policy, and trust terms.
- Health and readiness: validate connector participation, profile compatibility, and required supporting services.
- Must never leak into core: Tractus-X-specific vocabulary as canonical semantics.

### `adapters/dataspace/gaiax`
- Ports to implement: Gaia-X trust, compliance, or catalog interactions required by procedures or packs.
- Local wire models: Gaia-X compliance or credential payloads, federation metadata, catalog shapes.
- Canonical mapping: translate Gaia-X-specific trust or compliance signals into core trust and compliance models.
- Health and readiness: validate federation services, trust chain material, and compliance endpoint availability.
- Must never leak into core: Gaia-X-specific credential or federation formats.

### `adapters/dataspace/basyx`
- Ports to implement: AAS registry, submodel, descriptor, and twin-facing operations.
- Local wire models: BaSyx server payloads, AAS descriptors, submodel service payloads.
- Canonical mapping: translate AAS resources into twin, schema-mapping, and DPP-related canonical models.
- Health and readiness: validate registry reachability, submodel availability, and version compatibility.
- Must never leak into core: BaSyx SDK types, AAS transport-specific pagination, or raw descriptor storage models.

### `adapters/enterprise/sap-odata`
- Ports to implement: enterprise extraction, schema discovery, data mapping input, and selective publication reads.
- Local wire models: OData entities, metadata documents, SAP-specific paging or auth details.
- Canonical mapping: convert enterprise entities into canonical mapping inputs or publishable source snapshots.
- Health and readiness: validate credential scope, metadata availability, and extraction performance assumptions.
- Must never leak into core: SAP entity names as canonical identifiers.

### `adapters/enterprise/siemens-teamcenter`
- Ports to implement: PLM extraction, bill-of-material access, document references, and lifecycle metadata retrieval.
- Local wire models: Teamcenter service payloads, object identities, session details.
- Canonical mapping: map parts, lifecycle state, and product structure into canonical twin, DPP, and mapping models.
- Health and readiness: validate session bootstrap, query scope, and target object reachability.
- Must never leak into core: Teamcenter object model assumptions.

### `adapters/enterprise/kafka-ingest`
- Ports to implement: event ingestion, event normalization, backfill hooks, and stream checkpointing.
- Local wire models: topic payloads, headers, partition metadata, offset tracking.
- Canonical mapping: normalize event payloads into canonical observability, metering, or DPP update inputs.
- Health and readiness: validate topic access, lag thresholds, schema compatibility, and checkpoint storage.
- Must never leak into core: partitioning, offset, or consumer-group mechanics.

### `adapters/enterprise/object-storage`
- Ports to implement: object listing, controlled fetch, artifact staging, and manifest generation.
- Local wire models: bucket metadata, object keys, storage-specific ACL or versioning metadata.
- Canonical mapping: expose objects as source artifacts, evidence references, or publication payload inputs.
- Health and readiness: validate bucket reachability, versioning assumptions, and least-privilege access.
- Must never leak into core: provider-specific storage semantics or ACL models.

### `adapters/enterprise/sql-extract`
- Ports to implement: query-based extraction, projection, snapshotting, and change capture input.
- Local wire models: SQL rows, database-specific type mappings, connection semantics.
- Canonical mapping: normalize query outputs into source mappings or canonical data snapshots.
- Health and readiness: validate connection scope, query explainability, and extraction consistency.
- Must never leak into core: vendor-specific SQL dialect details or connection pooling behavior.

### `adapters/infrastructure/keycloak`
- Ports to implement: operator IAM, role lookup, group assignment, service-account alignment where required.
- Local wire models: realm, client, role, token, and admin API payloads.
- Canonical mapping: translate identities and roles into `core/domains/operator-access` and `core/domains/tenant-topology` concepts.
- Health and readiness: validate realm reachability, client config, token exchange, and admin privileges.
- Must never leak into core: Keycloak realm naming or admin API DTOs.

### `adapters/infrastructure/vault-kms`
- Ports to implement: key-handle allocation, signing or decryption invocation, secret lease retrieval, rotation support.
- Local wire models: vault path conventions, transit or KMS payloads, secret lease metadata.
- Canonical mapping: return key references, trust handles, and rotation outcomes to `core/domains/machine-trust`.
- Health and readiness: validate mount reachability, policy scope, lease renewal, and auditability.
- Must never leak into core: path layouts, lease tokens, raw secret payloads.

### `adapters/infrastructure/temporal-client`
- Ports to implement: workflow start, signal, query, update, and result retrieval for runtime callers outside workers.
- Local wire models: Temporal client requests, task queue metadata, workflow execution identifiers.
- Canonical mapping: expose typed procedure invocation results and workflow handles without leaking SDK-specific behavior upward.
- Health and readiness: validate namespace connectivity, task queue routing, and version compatibility.
- Must never leak into core: SDK futures, workflow execution internals, or raw event history.

### `adapters/infrastructure/postgres`
- Ports to implement: persistence for canonical records, audit references, workflow metadata, or mapping state where relational storage is appropriate.
- Local wire models: SQL schema, row mappings, transaction semantics, migration details.
- Canonical mapping: map rows into canonical entities or repository return types.
- Health and readiness: validate connectivity, migration state, transaction settings, and backup expectations.
- Must never leak into core: table names as business semantics or ORM-specific model types.

### `adapters/infrastructure/telemetry`
- Ports to implement: metrics, traces, logs, event export, and health instrumentation sinks.
- Local wire models: telemetry exporter payloads, metric naming, trace context propagation, vendor sink details.
- Canonical mapping: translate canonical observability signals into sink-specific instrumentation without redefining meaning.
- Health and readiness: validate exporter reachability, sampling assumptions, and backpressure behavior.
- Must never leak into core: vendor sink configuration or metric backend query language.

## Allowed Dependencies
- `core/` ports, canonical models, and domain contracts
- `schemas/` pinned wire artifacts, validation documents, and JSON-LD contexts
- `packs/` profile overlays that change adapter behavior without changing canonical semantics
- `tests/` integration and compatibility suites
- `docs/` API and operational documentation for external systems

## Forbidden Shortcuts
- Do not return vendor DTOs or raw wire payloads to `core/`, `procedures/`, or `apps/`.
- Do not let transport retry policy or pagination state leak across the port boundary.
- Do not embed business-policy translation in adapter code when it belongs in `core/` or `packs/`.
- Do not log secrets, tokens, raw credentials, or trust-material content.
- Do not collapse composition adapters and leaf adapters into a single opaque package without documenting the layers.

## Build / Implementation Order
1. Confirm the `core/` port and canonical contract.
2. Pin or reference required schemas, contexts, and profile artifacts from `schemas/`.
3. Implement leaf adapters for the external transport or SDK.
4. Add composition adapters for ecosystem-specific or workflow-facing behavior.
5. Add health and readiness checks plus explicit error mapping.
6. Add integration and compatibility tests.
7. Document operational assumptions, secrets requirements, and profile compatibility.

## Required Tests / Verification
- Existing structural checks:
  - `find adapters -maxdepth 3 -type d | sort`
  - `test -f adapters/AGENTS.md`
  - `test -f docs/agents/adapters-agent.md`
- Expected command once scaffolded: `make test-adapters`
- Expected command once scaffolded: `pytest tests/integration -k adapters`
- Expected command once scaffolded: `pytest tests/compatibility/dsp-tck`
- Expected command once scaffolded: `pytest tests/compatibility/dcp-tck`

## Required Docs Updates
- Update `docs/api/` when external-facing adapter behavior or contracts change.
- Update `docs/runbooks/` when credentials, health checks, or operational recovery changes.
- Update `docs/arc42/` when integration topology or supported ecosystems change.
- Update `docs/agents/adapters-agent.md` and `adapters/AGENTS.md` when package boundaries move.

## Common Failure Modes
- Canonical layers start depending on vendor DTOs because adapter mapping was skipped.
- Secret handling is mixed with business logging and leaks token material.
- Transport errors are surfaced as opaque HTTP or SDK exceptions instead of typed outcomes.
- Composition adapters become indistinguishable from leaf transports.
- Health checks only verify network reachability and ignore profile or config compatibility.

## Handoff Contract
- Report which ports were implemented or changed.
- Identify affected adapter families and whether they are leaf or composition adapters.
- Describe canonical mappings, error mapping, readiness checks, and secret-handling implications.
- Report compatibility or profile risk, verification run, and required downstream docs or procedure updates.

## Done Criteria
- All wire models remain local to adapter packages.
- Upstream layers only see canonical or explicitly typed adapter results.
- Secret handling, readiness, and error mapping are explicit.
- Composition and leaf responsibilities remain clear.
- Compatibility and operational docs are updated.

## Example Prompts For This Agent
- "Implement the EDC negotiation adapter boundary for canonical contract offers without leaking EDC DTOs upstream."
- "Add a BaSyx adapter mapping from AAS descriptors into canonical twin registration inputs."
- "Create a Keycloak adapter contract for operator role lookup and document the health checks required."
