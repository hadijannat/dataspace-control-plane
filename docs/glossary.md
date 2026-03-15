---
title: "Glossary"
summary: "Definitions for all domain terms, protocol acronyms, regulatory references, and platform-specific concepts used across the dataspace control plane."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Glossary

All terms used across architecture documentation, runbooks, ADRs, and compliance mappings are defined here. For architecture-specific terms (Blast Radius, Evidence Envelope, etc.) see also [arc42/12-glossary.md](arc42/12-glossary.md).

## AAS (Asset Administration Shell)

The IDTA standard for digital twins. An AAS instance wraps a physical or logical asset with a standardized shell descriptor and a set of typed submodels. The platform uses AAS Release 25-01 to serialize Digital Product Passports and expose them via BaSyx AAS Server. See [IDTA](https://www.idtaschinema.org/).

## Bitstring Status List

A W3C specification for revocable Verifiable Credential status. A compressed bitstring is published at a known URL; each VC references a bit index within the list. When the bit is set, the VC is considered revoked. The platform uses Bitstring Status List to allow credential revocation without requiring per-credential registries.

## Canonical Model

The authoritative domain representation defined in `core/`. Every concept the platform operates on — companies, contracts, passports, metering events — has exactly one canonical representation in `core/`. Adapters, procedures, and packs must transform to and from canonical models; they may not define competing representations.

## Catena-X

The industrial dataspace for the automotive supply chain. Catena-X mandates the Eclipse Dataspace Connector (EDC) for data plane operations, ODRL 2.2 policies for data contracts, W3C VCs for participant identity, and the Dataspace Protocol (DSP) and Dataspace Connect Protocol (DCP) as wire protocols. The `packs/catenax/` module implements Catena-X-specific overlay rules.

## Control API

The FastAPI-based HTTP surface of the platform, located at `apps/control-api/`. It is the primary interface for operators, web-console, and machine integrations. It exposes an OpenAPI 3.1 specification at `docs/api/openapi/source/control-api.yaml` and implements RFC 7807 Problem Details for error responses.

## Core

The semantic kernel layer (`core/`). Defines domain meaning through canonical models, invariants, domain events, and audit primitives. Nothing outside `core/` may redefine what a concept means. The dependency rule is strict: `core/` has no runtime dependency on `adapters/`, `procedures/`, `apps/`, or `packs/`.

## DCP (Dataspace Connect Protocol)

The credential exchange protocol for EDC-based dataspaces. DCP defines how a participant presents Verifiable Credentials to gain access to data offers. The platform's `adapters/dataspace/dcp/` module normalizes DCP messages into core credential presentation events.

## DPP (Digital Product Passport)

The regulated digital record required under EU ESPR Regulation 2024/1781. A DPP captures product lifecycle data (materials, carbon footprint, repairability, end-of-life) and is submitted to an EU-operated registry. The platform implements DPP creation, lifecycle management, and registry submission via the `packs/espr_dpp/` overlay and `schemas/dpp/` schema family.

## DSP (Dataspace Protocol)

The Eclipse Dataspace Components wire protocol for catalog query, contract negotiation, and data transfer. DSP is the HTTP-based protocol that EDC connectors use to discover and negotiate access to datasets. The `adapters/dataspace/dsp/` module implements the DSP message normalizer.

## EDC (Eclipse Dataspace Connector)

The open-source reference implementation of the DSP and DCP protocols, maintained by the Eclipse Foundation. The platform operates alongside EDC connectors — the `apps/edc-extension/` module extends the EDC with platform-specific signing and policy evaluation hooks, while the `apps/provisioning-agent/` manages connector registration.

## ESPR (Ecodesign for Sustainable Products Regulation)

EU Regulation 2024/1781, which mandates Digital Product Passports for regulated product categories. ESPR replaces the Ecodesign Directive (2009/125/EC) and introduces the DPP as the primary compliance instrument. Delegated acts per product category are published separately and define the specific field requirements. See Risk R-04 in `docs/arc42/11-risks-and-technical-debt.md`.

## Gaia-X

The European federated data infrastructure initiative that defines a trust framework for data spaces. Gaia-X participants publish Self-Descriptions (JSON-LD documents) that describe their services and compliance with Gaia-X Trust Framework 22.10. The `packs/gaia_x/` module implements Self-Description generation and validation.

## IDTA (Industrial Digital Twin Association)

The standards body responsible for the Asset Administration Shell standard. IDTA publishes the AAS meta-model, submodel templates (SMT), and the AAS API specification. The platform targets IDTA AAS Release 25-01.

## Lineage

A mandatory field in enterprise-mapping field mappings (`schemas/enterprise-mapping/`) that records the full transformation chain from source system field to canonical model field. Lineage entries enable auditors to trace any canonical model value back to its source system origin, transformation function, and timestamp.

## Machine Trust

Service-to-service authentication using Keycloak client credentials flow combined with Vault Transit-signed tokens. Machine identities are Keycloak service accounts. They receive short-lived JWTs (15-minute TTL) via the `client_credentials` grant and use Vault Transit signing for any outbound signed artifacts. No long-lived shared secrets are used for machine auth.

## MADR

Markdown Architectural Decision Record. The format used for all ADRs in `docs/adr/`. MADR provides a lightweight, VCS-friendly structure: front matter (status, date, decision-makers), context, decision drivers, options considered, chosen option, consequences, and an optional confirmation section. See [adr.github.io/madr](https://adr.github.io/madr/).

## Metering

The usage-event tracking layer that records agreement-bound data consumption. When a contract agreement is active, every data access produces a metering event conforming to `schemas/metering/source/business/usage-record.schema.json`. Metering events accumulate in Kafka and are settled by the settlement service. Metering is a contractual and regulatory obligation for Catena-X participants.

## ODRL (Open Digital Rights Language)

W3C policy language used for Catena-X data contracts. ODRL 2.2 expresses permissions, prohibitions, and obligations on data offers and agreements. The `packs/catenax/` module provides Catena-X-specific ODRL policy profiles. Policies are stored and exchanged as JSON-LD and validated against `schemas/odrl/`.

## OSCAL

NIST Open Security Controls Assessment Language. A machine-readable format for expressing security controls, component definitions, system security plans, and assessment results. The platform uses OSCAL 1.1.2 YAML files in `docs/compliance-mappings/oscal/` to create auditable, machine-verifiable compliance artifacts for Catena-X participation and Battery Passport obligations.

## Pack

An overlay module in `packs/` that adds ecosystem-specific or regulation-specific rules without changing `core/` semantics. Packs implement a shared interface (reducer, manifest, validators) and are composable — multiple packs can apply simultaneously. Pack conflicts are declared explicitly in the reducer. See [ADR 0005](adr/0005-packs-as-pure-overlay.md).

## Procedure

A durable Temporal workflow in `procedures/` that implements a business process. Examples: `OnboardingWorkflow`, `ContractNegotiationWorkflow`, `DPPExportWorkflow`. Procedures emit evidence artifacts, update Postgres via activities, and interact with Vault, Keycloak, and external registries. Workflow code is the runbook — no separate compensating transaction scaffolding.

## Proof

A W3C Data Integrity proof attached to a Verifiable Credential or DID Document. The platform generates `DataIntegrityProof` proofs using the `ecdsa-sd-2023` or `eddsa-rdfc-2022` cryptosuites, with signing performed exclusively via Vault Transit. The proof is embedded in the `proof` field of the VC JSON-LD document.

## Schema Family

One of the six JSON Schema 2020-12 schema groups in `schemas/`: `vc` (W3C Verifiable Credentials), `odrl` (W3C ODRL 2.2 policies), `aas` (IDTA AAS Release 25-01), `dpp` (Digital Product Passport 4.0), `metering` (usage events and settlement records), `enterprise-mapping` (field mapping DSL). Each family has its own `$vocabulary` and `source/`, `derived/`, and `vendor/` subdirectories.

## STRIDE

The threat classification framework used in the platform threat model. STRIDE stands for: **S**poofing (impersonating a user or system), **T**ampering (modifying data or code), **R**epudiation (denying an action occurred), **I**nformation Disclosure (exposing data to unauthorized parties), **D**enial of Service (making a system unavailable), **E**levation of Privilege (gaining unauthorized access). See [threat-model/index.md](threat-model/index.md).

## Temporal

The durable workflow orchestration engine used for all multi-step business processes. Temporal provides: durable execution (workflows survive process restarts), replay safety (workflow history is immutable), and time-skipping test support via `WorkflowEnvironment.start_time_skipping()`. The platform uses the Temporal Python SDK. See [ADR 0002](adr/0002-adopt-temporal-as-workflow-engine.md).

## Tenant

An isolated organizational unit sharing platform infrastructure. Tenant isolation is enforced at three layers: (1) Keycloak realm-per-tenant for identity isolation, (2) Temporal workflow ID prefix `{tenant_id}:` for workflow scoping, and (3) PostgreSQL Row-Level Security policies as the final enforcement layer. Cross-tenant data access is architecturally impossible at the DB layer regardless of API-layer inputs.

## Transit Engine

HashiCorp Vault's Transit secrets engine. The Transit engine provides cryptographic operations (sign, verify, encrypt, decrypt, hash) without ever exporting the private key material. Keys are created with `exportable=false` and `allow_plaintext_backup=false`. The platform uses Transit as the exclusive signing boundary for VCs, DID Documents, and evidence artifacts. See [ADR 0004](adr/0004-vault-transit-for-signing-keys.md).

## VC (Verifiable Credential)

A W3C standard for cryptographically signed digital attestations. The platform issues and verifies VCs conforming to the W3C VC Data Model 2.0. VC types include `DataspaceParticipantCredential`, `MembershipCredential`, and `DPPIssuerCredential`. All VCs include a Data Integrity proof signed via Vault Transit and a Bitstring Status List credential status entry.

## Wave

One of four build stages in the multi-agent team model. Wave 0 (foundation-planning): core-lead, schemas-lead, infra-lead, docs-lead establish the semantic foundation. Wave 1 (platform-foundation): full canonical models, schema families, adapter integrations, infra packaging. Wave 2 (execution-layer): durable workflows, runtime app surfaces, integration verification. Wave 3 (overlays-hardening): ecosystem overlays, release gate hardening, governance completion. Each wave requires handoff artifacts from all teammates before closure.
