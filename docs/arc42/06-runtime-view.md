---
title: "6. Runtime View"
summary: "Dynamic behavior of the dataspace control plane: company onboarding, contract negotiation, and DPP export runtime scenarios."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

The runtime view documents the most important dynamic behaviors of the platform as sequence diagrams. Each scenario corresponds to a Temporal workflow in `procedures/`.

## Scenario 1: Company Onboarding

Company onboarding provisions a new tenant: creates a Keycloak realm, issues a DID document signed by Vault Transit, creates the Postgres tenant record with RLS, and returns the operator's credentials.

```mermaid
sequenceDiagram
    actor Operator
    participant WC as web-console
    participant CA as control-api
    participant TS as Temporal Server
    participant TW as temporal-workers
    participant KC as Keycloak
    participant VT as Vault Transit
    participant PG as PostgreSQL

    Operator->>WC: Submit company registration form
    WC->>CA: POST /api/v1/companies {legalEntityId, displayName}
    CA->>CA: Validate request body against Company schema
    CA->>TS: StartWorkflow(OnboardingWorkflow, company_id, tenant_id)
    CA-->>WC: 202 Accepted {workflowId, runId, statusUrl}
    WC-->>Operator: "Provisioning in progress..." + status poll

    TS->>TW: Schedule OnboardingWorkflow

    TW->>KC: CreateRealm(tenant_id)
    KC-->>TW: realm created

    TW->>KC: CreateClient(control-api, provisioning-agent)
    KC-->>TW: client_id, client_secret (ephemeral, written to Vault)

    TW->>VT: CreateKey(tenant_id-signing, exportable=false)
    VT-->>TW: key_id (no private material returned)

    TW->>VT: Sign(DID document JSON, key_id)
    VT-->>TW: signature bytes (key never leaves Vault)

    TW->>PG: INSERT tenant(tenant_id, did, realm, status='provisioned') [RLS enforced]
    PG-->>TW: success

    TW->>TS: CompleteWorkflow(company_id, did, realm, status)

    Operator->>WC: Poll GET /api/v1/companies/{companyId}
    WC->>CA: GET /api/v1/companies/{companyId}
    CA->>PG: SELECT company WHERE company_id=? [RLS applied]
    PG-->>CA: company record
    CA-->>WC: 200 {companyId, status: "provisioned", did}
    WC-->>Operator: Onboarding complete — DID and realm displayed
```

**Key invariants:**

- `client_secret` is written to Vault immediately after Keycloak creates it; it is never logged or stored in Postgres.
- The DID document is signed before the tenant record is written; if signing fails, the tenant record is never created.
- The workflow is idempotent: if restarted after Postgres write, the existing record is returned.

## Scenario 2: Contract Negotiation

Contract negotiation implements the DSP negotiation state machine: offer → agreed → verified → finalized. An ODRL policy offer from a Catena-X partner is evaluated, a DCP credential presentation is required, and the agreement is recorded in Postgres.

```mermaid
sequenceDiagram
    actor Operator
    participant CA as control-api
    participant TS as Temporal Server
    participant TW as temporal-workers
    participant DSP as DSP adapter
    participant DCP as DCP adapter
    participant EDC as EDC Connector
    participant CX as Catena-X Partner EDC
    participant VT as Vault Transit
    participant PG as PostgreSQL

    Operator->>CA: POST /api/v1/contracts/negotiations {assetId, counterpartyId, policyOffer}
    CA->>TS: StartWorkflow(ContractNegotiationWorkflow, negotiation_id)
    CA-->>Operator: 202 Accepted {negotiationId, statusUrl}

    TS->>TW: Schedule ContractNegotiationWorkflow

    TW->>DSP: SendContractRequest(assetId, policyOffer) to counterparty DSP endpoint
    DSP->>EDC: DSP ContractRequestMessage (JSON-LD)
    EDC->>CX: DSP ContractRequestMessage
    CX-->>EDC: DSP ContractOfferMessage (with ODRL policy)
    EDC-->>DSP: ContractOfferMessage

    TW->>TW: EvaluateODRLPolicy(policy, catena-x pack profile)
    Note over TW: packs/catenax/ checks policy constraints

    TW->>DCP: RequestCredentialPresentation(counterparty, required_vc_types)
    DCP->>CX: DCP CredentialRequestMessage
    CX-->>DCP: W3C VerifiablePresentation (MembershipCredential)
    DCP-->>TW: credential_presentation

    TW->>TW: VerifyCredentialPresentation(vp, issuer_did)
    TW->>VT: Verify(signature, credential_body, key_id)
    VT-->>TW: verification_result

    TW->>DSP: SendContractAgreement(agreement_id, policy)
    DSP->>CX: DSP ContractAgreementMessage

    TW->>PG: INSERT agreement(agreement_id, tenant_id, asset_id, policy_hash, status='finalized') [RLS]
    TW->>PG: INSERT metering_context(agreement_id, tenant_id, start_time)

    TW->>TS: CompleteWorkflow(agreement_id, status='finalized')
```

## Scenario 3: DPP Passport Export

The DPP export workflow applies the Battery Passport or ESPR pack, serializes the passport as an AAS shell, submits it to the EU DPP registry, and emits evidence.

```mermaid
sequenceDiagram
    actor Operator
    participant CA as control-api
    participant TS as Temporal Server
    participant TW as temporal-workers
    participant BP as Battery Passport Pack
    participant AAS as AAS adapter
    participant BaSyx as BaSyx AAS Server
    participant DPPR as EU DPP Registry
    participant VT as Vault Transit
    participant PG as PostgreSQL
    participant KF as Kafka

    Operator->>CA: POST /api/v1/passports/{passportId}/lifecycle-transitions {targetState: "published"}
    CA->>TS: StartWorkflow(DPPExportWorkflow, passport_id, tenant_id)
    CA-->>Operator: 202 Accepted {workflowId, statusUrl}

    TS->>TW: Schedule DPPExportWorkflow

    TW->>PG: SELECT passport WHERE passport_id=? [RLS enforced]
    PG-->>TW: passport canonical model

    TW->>BP: ApplyBatteryPassportRules(passport, annex_xiii_tier_config)
    BP-->>TW: enriched_passport (all Annex XIII fields validated)

    TW->>AAS: SerializeAsAASShell(enriched_passport)
    AAS-->>TW: aas_shell_descriptor (JSON)

    TW->>BaSyx: PUT /shells/{aasId} (shell descriptor)
    BaSyx-->>TW: 201 Created

    TW->>VT: Sign(evidence_envelope_json, key_id)
    VT-->>TW: signed_evidence (proof embedded)

    TW->>DPPR: POST /passports {aas_shell_ref, evidence_envelope}
    DPPR-->>TW: registry_id, submission_timestamp

    TW->>PG: UPDATE passport SET status='published', registry_id=? [RLS]
    TW->>PG: INSERT evidence_record(passport_id, evidence_envelope, signed_at) [append-only]

    TW->>KF: Publish metering.usage-record {passport_id, tenant_id, operation='dpp-export', timestamp}
    KF-->>TW: offset acked

    TW->>TS: CompleteWorkflow(passport_id, registry_id, status='published')
    Operator->>CA: GET /api/v1/passports/{passportId}
    CA-->>Operator: 200 {status: "published", registryId, evidenceRef}
```

**Key invariants:**

- Evidence is signed before registry submission; if signing fails, the workflow retries the sign activity (idempotent via Vault key_id + payload hash).
- The metering event is published after Postgres commit; if Kafka publish fails, the activity retries — the usage-record schema includes an idempotency key.
- Evidence records are append-only; no UPDATE on the evidence table is permitted.
