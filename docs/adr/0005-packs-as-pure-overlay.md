---
title: "Packs as pure overlays over core semantics — no pack may redefine core domain concepts"
summary: "Architecture decision record establishing packs as overlays over core semantics."
owner: docs-lead
last_reviewed: "2026-03-16"
status: accepted
date: 2026-03-14
decision-makers:
  - packs-lead
  - core-lead
consulted:
  - procedures-lead
  - adapters-lead
  - schemas-lead
  - all-leads
informed:
  - all-leads
---

## Context and Problem Statement

The platform must simultaneously support multiple overlapping regulatory regimes and ecosystem protocols: Catena-X (ODRL policies, VCs, DSP/DCP protocol), Gaia-X (Self-Descriptions, trust labels), Battery Passport (EU Regulation 2023/1542, Annex XIII field tiers), ESPR DPP (EU Regulation 2024/1781), and Manufacturing-X (sector-specific extensions).

Each of these regimes defines rules about what a valid data-sharing agreement, digital product passport, or participant credential looks like. The rules overlap: a Battery Passport submitted through a Catena-X connector must satisfy both Battery Regulation Annex XIII completeness rules and Catena-X ODRL policy rules simultaneously.

Without a disciplined model for composing these rules, two failure modes emerge:

1. **Core pollution**: regulatory rules are embedded in `core/`, making `core/` incomprehensible and preventing reuse of core types without all regulatory rules applying.
2. **Forking**: each regulation gets its own copy of `Company`, `Passport`, or `Agreement` types, with no shared canonical model — making cross-regulation workflows impossible without complex type mapping.

## Decision Drivers

* Multi-ecosystem support without forking: the same canonical model instance must be operable under multiple regulatory regimes simultaneously
* Core semantic stability: `core/` must remain comprehensible and minimal — adding a new regulation must not require modifying `core/`
* Pack conflict detection: if two packs have conflicting rules for the same field, the conflict must be surfaced explicitly, not silently resolved
* Composability: multiple packs must be applicable to the same canonical model instance in a single operation via a shared reducer
* Testability: each pack must be testable in isolation without deploying the full platform
* Dependency on `core/` only: packs must depend on `core/` types and `schemas/` but must not depend on `adapters/`, `procedures/`, or `apps/`

## Considered Options

* Packs as pure overlays over core (chosen)
* Packs as independent canonical model owners (each pack defines its own types)
* Ecosystem logic embedded directly in adapters
* Single monolithic regulatory module in `core/`

## Decision Outcome

**Chosen option: "Packs as pure overlays over core"**, because it is the only model that satisfies all decision drivers. Each pack in `packs/` receives a canonical model instance from `core/`, applies its overlay rules (field enrichment, validation, constraint injection), and returns the enriched instance or a list of validation errors. The `PackReducer` in `packs/_shared/reducers/` applies multiple packs in dependency order and surfaces `PackConflict` errors when two packs declare incompatible rules for the same field. No pack may introduce a new canonical type — it may only reference or constrain existing core types. See [arc42/04-solution-strategy.md](../arc42/04-solution-strategy.md) for the strategic rationale and [arc42/08-crosscutting-concepts.md](../arc42/08-crosscutting-concepts.md) for the canonical model crosscutting concept.

### Positive Consequences

* Adding a new regulation or ecosystem requires writing a new pack, not modifying `core/` or any existing pack
* `PackReducer` enables simultaneous application of `battery_passport` + `espr_dpp` + `catenax` packs to a single `Passport` instance
* Pack isolation: each pack is testable with a synthetic `core/` fixture without deploying adapters or procedures
* Conflict detection: `PackConflict` surfaces incompatible rules at pack composition time, before any external side effect
* Pack versioning is independent of core versioning — a pack can be updated to reflect a new delegated act without bumping the core model version

### Negative Consequences

* Pack interface contract (`PackInterface`, `PackManifest`, `PackReducer`) must be stable — changing it requires updating all 5 packs simultaneously
* Some regulatory rules require access to external state (e.g., checking whether a BattID has been registered) — these must be implemented as activities in `procedures/` that call pack validators, not as pack validators that make network calls directly
* Pack dependency ordering in the reducer must be declared explicitly in each pack's `PackManifest` — getting this wrong can cause rules to be applied in the wrong order

### Confirmation

`tests/unit/packs/reducers/` suite verifies: (1) all 5 packs reduce correctly on conforming fixtures; (2) `PackConflict` is raised when two packs declare conflicting `required_field` rules for the same field path; (3) reducer dependency ordering matches manifest declarations.

## Pros and Cons of the Options

### Packs as Pure Overlays over Core

Each pack implements `PackInterface`: `apply(canonical_model) -> (enriched_model, errors)`. The `PackReducer` composes multiple packs in dependency order.

* Good, because `core/` remains minimal and stable — no regulatory noise
* Good, because multi-pack composition is handled by a single well-tested `PackReducer`
* Good, because pack isolation enables fast, dependency-free pack unit tests
* Good, because explicit conflict detection surfaces incompatible rules
* Bad, because pack interface contract must be backward-compatible — breaking changes require coordinated updates
* Bad, because external-state-dependent rules must be lifted out of packs into procedure activities

### Packs as Independent Canonical Model Owners

Each pack defines its own `BatteryPassportModel`, `ESPRPassportModel`, etc. Cross-regulation workflows use type mapping.

* Good, because each pack is fully autonomous — no shared interface contract to maintain
* Bad, because type mapping between pack-owned models grows O(n²) with the number of packs
* Bad, because no shared canonical model means cross-regulation workflows require multi-step type translation
* Bad, because `core/` becomes a thin type alias layer — semantic kernel purpose is lost

### Ecosystem Logic Embedded in Adapters

Regulatory rules are implemented directly in the adapter modules (`adapters/dataspace/`, `adapters/aas/`).

* Good, because rules are co-located with the protocol they apply to
* Bad, because Catena-X rules would be in the DSP adapter, but the same rules must also apply during DPP export (which uses the AAS adapter) — rules must be duplicated
* Bad, because adapter layer has no mechanism for cross-adapter rule composition
* Bad, because adapters are integration components — embedding regulatory semantics in them violates the layer architecture

### Single Monolithic Regulatory Module in core/

All regulatory rules (Battery Passport, ESPR, Catena-X, Gaia-X, Manufacturing-X) live in `core/regulatory/`.

* Good, because a single location for all regulatory rules
* Bad, because `core/` becomes coupled to every regulation — adding Manufacturing-X requires modifying the semantic kernel
* Bad, because regulatory rules have external state dependencies (registry lookups) that must not appear in `core/`
* Bad, because pack conflict detection is impossible when all rules are in a single module with implicit priority
