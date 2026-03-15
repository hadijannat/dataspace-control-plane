---
title: "Catena-X Compliance Narrative"
summary: "How the platform satisfies Catena-X Operating Model 4.0 obligations and DSP/DCP protocol requirements for dataspace participation."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Catena-X Compliance Narrative

## Obligation Source

- **Catena-X Operating Model 4.0** — defines the rules for network participation, onboarding, and data sharing
- **DSP (Dataspace Protocol)** — Eclipse Dataspace Components wire protocol for catalog, negotiation, and transfer
- **DCP (Dataspace Connect Protocol)** — credential exchange protocol for access gating
- **ODRL 2.2 Policy Profiles** — Catena-X-specific ODRL constraints and permissions vocabulary

## Key Obligations

### CX-DSP-01: DSP Catalog Endpoint

Every Catena-X participant must expose a DSP-compliant catalog endpoint that responds to `POST /catalog/request` messages in JSON-LD format. The catalog lists data offers with associated ODRL policies.

**Platform component**: `adapters/dataspace/dsp/` normalizes DSP catalog request messages into canonical `CatalogQuery` events. The `apps/edc-extension/` wires the DSP handler into the EDC connector framework.

**Status**: Scaffolded — DSP adapter directory structure created; catalog handler implementation pending (Wave 2).

**Schema reference**: `schemas/odrl/source/base/policy-offer.schema.json` defines the ODRL policy offer shape that catalog responses must include.

### CX-DCP-01: DCP Credential Service

Participants must expose a DCP credential service that accepts `CredentialRequest` messages and returns W3C Verifiable Presentations containing at minimum a `DataspaceParticipantCredential` and a `MembershipCredential`.

**Platform component**: `adapters/dataspace/dcp/` normalizes DCP credential request messages. `procedures/trust/` implements the `CredentialIssuanceWorkflow` that issues the required VCs via Vault Transit signing.

**Status**: DCP adapter scaffolded; VC issuance workflow pending (Wave 2).

**Schema reference**: `schemas/vc/source/envelope/credential-envelope.schema.json` defines the VC envelope. `schemas/vc/source/profiles/participant-credential.schema.json` defines the `DataspaceParticipantCredential` subject claims.

### CX-ODRL-01: ODRL Policy Evaluation

Data offers and contract negotiations must include ODRL 2.2 policies evaluated against the Catena-X policy profile vocabulary (e.g., `cx:BPN`, `cx:UsagePurpose`, `cx:FrameworkAgreement`).

**Platform component**: `packs/catenax/policy_profile/` defines the Catena-X ODRL constraint vocabulary. The `PackReducer` applies Catena-X policy rules during the `ContractNegotiationWorkflow`.

**Status**: ODRL parser and policy profile structure implemented in `packs/catenax/`. Integration with `ContractNegotiationWorkflow` pending (Wave 2).

**Schema reference**: `schemas/odrl/source/base/policy-offer.schema.json`, `schemas/odrl/source/base/policy-agreement.schema.json`.

### CX-VC-01: VC-Based Member Onboarding

New participants must receive a `DataspaceParticipantCredential` and a `MembershipCredential` issued by the Catena-X CA (or a delegated issuer) during onboarding. These credentials are presented in DCP exchanges to prove network membership.

**Platform component**: `procedures/trust/` implements `OnboardingWorkflow` which includes VC issuance. `adapters/infra/vault/` provides Vault Transit signing for the credential proof. `packs/catenax/` defines the VC type and subject claim requirements.

**Status**: Workflow structure defined; VC issuance activity pending (Wave 2).

**Schema reference**: `schemas/vc/source/envelope/credential-envelope.schema.json`.

## Gap Status Table

| Obligation | Obligation ID | Status | Gap description |
|-----------|--------------|--------|----------------|
| DSP catalog endpoint | CX-DSP-01 | Scaffolded | Catalog handler implementation pending in apps/edc-extension/ |
| DCP credential service | CX-DCP-01 | Scaffolded | VC issuance workflow pending in procedures/trust/ |
| ODRL policy evaluation | CX-ODRL-01 | Partial | Pack structure implemented; workflow integration pending |
| VC-based member onboarding | CX-VC-01 | Scaffolded | Onboarding activity implementation pending |
| DSP contract negotiation | CX-DSP-02 | Scaffolded | Negotiation workflow pending in procedures/ |
| DSP data transfer | CX-DSP-03 | Not started | EDC data plane integration pending |

## Protocol Conformance Testing

Conformance with DSP and DCP is verified by the `tests/compatibility/dsp-tck/` and `tests/compatibility/dcp-tck/` TCK suites. These suites use the Eclipse Foundation's official TCK test vectors.

**Current status**: TCK directories scaffolded; TCK test artifacts and running EDC counterparty in staging are not yet available (Risk R-02 in `docs/arc42/11-risks-and-technical-debt.md`).

## Schema References

| Schema file | Use |
|------------|-----|
| `schemas/odrl/source/base/policy-offer.schema.json` | ODRL policy offer validation in DSP catalog responses |
| `schemas/odrl/source/base/policy-agreement.schema.json` | ODRL policy agreement validation after negotiation |
| `schemas/vc/source/envelope/credential-envelope.schema.json` | W3C VC 2.0 envelope for all issued credentials |
| `schemas/vc/source/profiles/participant-credential.schema.json` | DataspaceParticipantCredential subject claims |
