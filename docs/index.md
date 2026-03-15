---
title: "Dataspace Control Plane"
summary: "Homepage and orientation guide for the dataspace control plane documentation site."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Dataspace Control Plane

The **Dataspace Control Plane** is a multi-ecosystem industrial data sharing platform that enables organizations to participate in regulated dataspaces (Catena-X, Gaia-X, Manufacturing-X) and comply with EU product regulations (Battery Passport under Regulation 2023/1542, Digital Product Passports under ESPR Regulation 2024/1781).

The platform provides a unified control surface for credential issuance, ODRL policy negotiation, Digital Product Passport lifecycle management, and durable workflow orchestration — all under strict tenant isolation and cryptographic audit.

## Key Capabilities

- **Multi-ecosystem dataspace participation**: Catena-X DSP/DCP protocol compliance, Gaia-X trust framework self-descriptions, Manufacturing-X connector interoperability, and ODRL 2.2 policy evaluation.
- **EU product regulation compliance**: Battery Passport (Annex XIII field tiers), ESPR Digital Product Passport creation and registry submission, and evidence emission conforming to machine-readable OSCAL component definitions.
- **Durable workflow orchestration**: Temporal-based business workflows survive infrastructure failures without compensating transaction scaffolding. Workflow code is the runbook.
- **Attribute-based access control**: Keycloak realm-per-tenant model with short-lived JWTs, Vault Transit for all signing operations (keys never externalized), and PostgreSQL RLS as the final tenant isolation enforcement layer.

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Architecture (arc42)](arc42/index.md) | 12-section arc42 architecture documentation including runtime scenarios, deployment view, quality requirements, and risk register |
| [Architecture Decisions (ADR)](adr/index.md) | MADR-format decision records for all load-bearing architectural choices |
| [API Reference](api/index.md) | OpenAPI 3.1 spec, authentication guide, idempotency, workflow handles, SSE, and error model |
| [Runbooks](runbooks/index.md) | Incident, platform, procedure, and external-dependency runbooks with triage checklists and remediation steps |
| [Threat Model](threat-model/index.md) | STRIDE-classified threats, trust boundary assumptions, and mitigation tracking |
| [Compliance Mappings](compliance-mappings/index.md) | Catena-X, ESPR DPP, and Battery Passport obligation narratives and OSCAL component definitions |
| [Style Guide](style-guide.md) | Authoring rules for contributors to this documentation site |
| [Glossary](glossary.md) | Definitions for all domain terms, protocol acronyms, and regulatory references |

## Repository Layer Map

| Directory | Layer | Role |
|-----------|-------|------|
| `core/` | Semantic kernel | Canonical domain models, invariants, domain events, audit primitives. Defines meaning — nothing else may. |
| `schemas/` | Contract registry | JSON Schema 2020-12 families (vc, odrl, aas, dpp, metering, enterprise-mapping), pinned upstream artifacts, provenance. |
| `adapters/` | Integration | Protocol normalization for EDC, DSP, DCP, Gaia-X, AAS, enterprise APIs, Kafka. Implements core ports. |
| `procedures/` | Durable orchestration | Temporal workflows, state machines, evidence emission. No integration logic. |
| `apps/` | Runtime surfaces | Thin compositional entrypoints: control-api (FastAPI), temporal-workers, web-console (Next.js), edc-extension, provisioning-agent. |
| `packs/` | Ecosystem overlays | Catena-X, Gaia-X, Manufacturing-X, ESPR-DPP, Battery Passport regulatory rules. Pure overlays over core. |
| `infra/` | Delivery substrate | Helm charts, Terraform modules, Docker images, OTel Collector configuration. |
| `tests/` | Verification | pytest suites: unit, integration, e2e, tenancy, crypto-boundaries, chaos, DSP/DCP TCK compatibility. |
| `docs/` | Governance | Architecture documentation, ADRs, API reference, runbooks, threat models, compliance mappings (this site). |

## Dependency Flow

```
schemas/ ──► core/ ──► procedures/ ──► apps/
  │                 └──► adapters/  ──► apps/
  │                 └──► packs/     ──► apps/
  │
  └──► tests/ (consumes all layers)
  └──► docs/  (documents all layers)
```

!!! note "Authoring Rules"
    Before contributing to this documentation site, read the [Style Guide](style-guide.md). Key rules: required front matter on every page, relative Markdown links only, Mermaid fenced blocks for all diagrams, one ADR per file using the MADR template.
