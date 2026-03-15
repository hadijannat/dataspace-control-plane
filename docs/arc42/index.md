---
title: "Architecture Documentation (arc42)"
summary: "Index and orientation for the 12-section arc42 architecture documentation of the dataspace control plane."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Architecture Documentation (arc42)

This section documents the platform architecture using the [arc42 template](https://arc42.org/), a proven 12-section structure for communicating software and system architecture. arc42 is technology-agnostic and explicitly designed for living documentation — it is maintained alongside code, not after the fact.

This is the **living architecture documentation**. It is updated whenever architectural decisions change, new layers are scaffolded, or runtime behavior is refined. For the decision log, see the [ADR index](../adr/index.md).

## Sections

| Section | Title | Description |
|---------|-------|-------------|
| [1](01-introduction-and-goals.md) | Introduction and Goals | Quality goals, stakeholders, and requirements overview |
| [2](02-constraints.md) | Constraints | Technical, regulatory, and organizational constraints that shape the design |
| [3](03-context-and-scope.md) | Context and Scope | System boundary, external actors, and technical interfaces |
| [4](04-solution-strategy.md) | Solution Strategy | Fundamental architectural bets and rationale |
| [5](05-building-block-view.md) | Building Block View | Static decomposition: layers, modules, schema families, packs |
| [6](06-runtime-view.md) | Runtime View | Dynamic behavior: onboarding, contract negotiation, DPP export |
| [7](07-deployment-view.md) | Deployment View | Kubernetes namespace layout, infrastructure provisioning order |
| [8](08-crosscutting-concepts.md) | Crosscutting Concepts | Multi-tenancy, durable execution, canonical model, audit, machine trust, observability, schema governance |
| [9](09-architecture-decisions.md) | Architecture Decisions | Index of all MADR ADRs with status and affected layers |
| [10](10-quality-requirements.md) | Quality Requirements | Quality tree, scenarios, and response measures |
| [11](11-risks-and-technical-debt.md) | Risks and Technical Debt | Current risk register with probability, impact, mitigation, and owner |
| [12](12-glossary.md) | Glossary | Architecture-specific terms not in the main glossary |

## How to Use This Documentation

- **Operators** building on the platform: start with [Section 3 (Context)](03-context-and-scope.md) and [Section 7 (Deployment)](07-deployment-view.md).
- **Developers** extending the platform: start with [Section 5 (Building Blocks)](05-building-block-view.md) and [Section 8 (Crosscutting Concepts)](08-crosscutting-concepts.md).
- **Auditors and compliance reviewers**: start with [Section 1 (Goals)](01-introduction-and-goals.md) and [Section 10 (Quality Requirements)](10-quality-requirements.md), then consult [Compliance Mappings](../compliance-mappings/index.md).
- **Security reviewers**: start with [Section 8 (Crosscutting)](08-crosscutting-concepts.md) and cross-reference the [Threat Model](../threat-model/index.md).

!!! note "Update Protocol"
    Every teammate who changes a trust boundary, adds a layer dependency, modifies an external interface, or changes deployment topology must update the relevant arc42 section as part of the same task. See [Style Guide](../style-guide.md) for authoring rules.
