---
title: "12. Glossary (Architecture-Specific)"
summary: "Architecture-specific terms used in the arc42 documentation that are not covered by the main repo glossary."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

For general domain terms, protocol acronyms, and regulatory references, see the [repo-wide glossary](../glossary.md). This section defines terms that are specific to the arc42 architecture documentation and the platform's internal structure.

## Blast Radius

The scope of impact if a given infrastructure component fails or is compromised. Used in runbooks and risk descriptions to characterize how much of the platform is affected by a failure. For example: "Vault sealed → blast radius: all signing operations fail; DPP export and onboarding workflows stall." Blast radius drives the severity classification of incidents and runbooks.

## Evidence Envelope

A structured artifact emitted by a Temporal workflow activity to record that a regulated action occurred. An evidence envelope conforms to `schemas/dpp/source/exports/evidence-envelope.schema.json` and contains: action type, actor (tenant_id + service account ID), timestamp, payload hash (SHA-256 of the regulated artifact), and a W3C Data Integrity proof signed via Vault Transit. Evidence envelopes are written to the append-only `evidence_records` Postgres table and are the primary audit artifact for compliance inspections.

## Handoff Artifact

A Markdown file written by a specialist owner before going idle, located at `.claude/handoffs/<dir>.md`. Handoff artifacts record: scope completed, files changed, verification run, design and contract changes, downstream impact, blockers, and recommended next tasks. The agent idle gate hook enforces handoff creation. No wave can close without all handoffs present. See `.claude/handoffs/README.md` for the template.

## Root Module (Terraform)

A Terraform configuration directory in `infra/terraform/roots/` that represents a deployable infrastructure scope. Root modules are applied independently via `terraform apply`. Examples: `infra/terraform/roots/bootstrap/` (DNS, VPC, TLS bootstrap), `infra/terraform/roots/platform/` (Postgres, Keycloak, Vault, Kafka), `infra/terraform/roots/observability/` (Prometheus, Grafana, Loki). Root modules call reusable child modules from `infra/terraform/modules/`.

## Pack Reducer

The composable rule application engine in `packs/_shared/reducers/`. The `PackReducer` takes a canonical model instance and a list of active packs (e.g., `[battery_passport, espr_dpp, catenax]`) and applies each pack's rules in dependency order, collecting validation errors and field enrichments. If two packs declare conflicting rules for the same field, the conflict is surfaced as a `PackConflict` error rather than silently resolved. The reducer is the only code path allowed to apply pack rules to a canonical model.

## Semantic Kernel

The `core/` layer, which functions as the semantic kernel of the platform. "Semantic kernel" emphasizes that `core/` defines the meaning of domain concepts (not just their structure). An adapter may have a wire model that looks like a company record, but it is not a company in the platform's domain until it has been transformed into the canonical `Company` type defined in `core/`. The semantic kernel is stable: adding new fields to a core type is acceptable; changing the meaning of an existing field requires an ADR.

## Wire Model

A data structure defined in an adapter (`adapters/`) that represents the format of a protocol message as received or sent over the wire. Wire models are distinct from canonical models: a DSP ContractRequestMessage is a wire model; after normalization by the DSP adapter, it becomes a `ContractRequest` canonical model in `core/`. Wire models must validate against the relevant schema family (e.g., `schemas/odrl/` for ODRL wire messages) before normalization. Wire models must not escape the adapter layer — procedures and apps work exclusively with canonical models.
