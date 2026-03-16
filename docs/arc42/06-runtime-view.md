---
title: "6. Runtime View"
summary: "Dynamic behavior of the dataspace control plane: company onboarding, contract negotiation, and DPP export runtime scenarios."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

The runtime view documents the most important dynamic behaviors of the platform as sequence diagrams. Each scenario corresponds to a Temporal workflow in `procedures/`.

## Scenario 1: Company Onboarding

Company onboarding starts through the generic procedure API, uses a manifest
derived business-key workflow ID, persists durable HTTP idempotency state, and
returns a workflow handle immediately. The workflow then provisions a tenant,
bootstraps wallet and connector state, conditionally binds hierarchy when
`parent_bpnl` is provided, and reports live phase and progress through a
workflow query.

```mermaid
sequenceDiagram
    actor Operator
    participant CA as control-api
    participant PG as PostgreSQL
    participant TS as Temporal Server
    participant TW as temporal-workers
    participant KC as Keycloak
    participant VT as Vault Transit
    participant SSE as SSE client

    Operator->>CA: POST /api/v1/operator/procedures/start
    Note over Operator,CA: procedure_type=company-onboarding,<br/>tenant_id, legal_entity_id,<br/>payload includes contact_email,<br/>connector_url, parent_bpnl?
    CA->>CA: Validate payload against ProcedureDefinition
    CA->>PG: UPSERT http_idempotency_keys(...)
    CA->>TS: StartWorkflow(CompanyOnboardingWorkflow, workflow_id="company-onboarding:{tenant_id}:{legal_entity_id}")
    CA-->>Operator: 202 Accepted {workflow_id, status:"running", poll_url, stream_url}
    Operator->>CA: POST /api/v1/streams/tickets {workflow_id}
    CA-->>Operator: 200 {ticket, expires_in_seconds}
    Operator->>SSE: Open EventSource with workflow-scoped ticket

    TS->>TW: Schedule CompanyOnboardingWorkflow

    TW->>KC: CreateRealm(tenant_id)
    KC-->>TW: realm created

    TW->>KC: CreateClient(control-api, provisioning-agent)
    KC-->>TW: client_id, client_secret (ephemeral, written to Vault)

    TW->>VT: CreateKey(tenant_id-signing, exportable=false)
    VT-->>TW: wallet_ref, wallet_did

    alt parent_bpnl present
        TW->>PG: Bind hierarchy(parent_bpnl, bpnl)
        PG-->>TW: hierarchy bound
    else parent_bpnl absent
        TW->>TW: Mark hierarchy_skipped
    end

    TW->>PG: UPSERT procedures(status, phase, progress_percent, links)
    PG-->>TW: projection updated
    TW-->>SSE: status event {status:"running", phase:"technical_integration_completed", progress_percent:60}

    TW->>TS: CompleteWorkflow(workflow_id, wallet_did, registration_ref, compliance_ref)

    Operator->>CA: GET /api/v1/operator/procedures/{workflow_id}
    CA-->>Operator: 200 {status:"completed", result:{wallet_did,...}}
    TW-->>SSE: status event {status:"completed", progress_percent:100}
```

**Key invariants:**

- `client_secret` is written to Vault immediately after Keycloak creates it; it is never logged or stored in Postgres.
- Wallet bootstrap persists both `wallet_ref` and the externally visible `wallet_did`; the workflow result returns the DID, not the internal reference.
- Hierarchy binding is authoritative on the activity result: when `parent_bpnl` is absent, onboarding skips the hierarchy-bound phase instead of claiming success.
- The API rejects duplicate active onboarding runs for the same `{tenant_id, legal_entity_id}` business key with `409`.

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
