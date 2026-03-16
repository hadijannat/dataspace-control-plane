---
title: "Threat Model"
summary: "Platform-wide threat model using STRIDE classification — methodology, scope, trust boundary assumptions, and mitigation tracking index."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

## Methodology

The platform threat model uses the [OWASP threat modeling process](https://owasp.org/www-community/Threat_Modeling) with STRIDE classification for individual threats. STRIDE classifies threats as: **S**poofing, **T**ampering, **R**epudiation, **I**nformation Disclosure, **D**enial of Service, **E**levation of Privilege.

The threat model is maintained in two formats:

1. **Narrative mitigations** (this section): human-readable threat tables with mitigation descriptions and evidence links.
2. **OWASP Threat Dragon JSON source models** (`threat-dragon/*.json`): machine-readable Data Flow Diagrams for visual review using the Threat Dragon desktop app.

## Scope

| Model | File | Coverage |
|-------|------|---------|
| Platform (full DFD) | [threat-dragon/platform.json](threat-dragon/platform.json) | All platform components and trust boundaries: control-api, temporal-workers, Vault, Keycloak, Postgres, external connectors |
| Onboarding flow | [threat-dragon/onboarding.json](threat-dragon/onboarding.json) | Company onboarding workflow: Operator → web-console → control-api → Temporal → Keycloak → Vault → Postgres |
| Contract negotiation | [threat-dragon/negotiation.json](threat-dragon/negotiation.json) | DSP negotiation flow: control-api → EDC connector → Catena-X partner → ODRL evaluation → DCP credential exchange |
| DPP provisioning | [threat-dragon/dpp-provisioning.json](threat-dragon/dpp-provisioning.json) | DPP export workflow: Temporal workers → AAS serialization → EU DPP registry submission |
| Machine trust | [threat-dragon/machine-trust.json](threat-dragon/machine-trust.json) | JWT validation, stream-ticket issuance, and inbound webhook authenticity |

## Review Cadence

- **Mandatory review**: After any architectural change to trust boundaries (new external interface, new auth mechanism, new data store)
- **Mandatory review**: Before each production release
- **Scheduled review**: Quarterly, aligned with the wave review sessions
- **Event-triggered review**: After any security incident that reveals a new threat class

Review notes are stored under `threat-model/reviews/`. The current baseline is
[2026-03-16-baseline-review.md](reviews/2026-03-16-baseline-review.md).

## Trust Boundary Assumptions

See [assumptions.md](assumptions.md) for the full list. Key assumptions:

1. Vault is initialized, unsealed, and has audit logging enabled before platform startup.
2. Network policies restrict Vault API and Keycloak Admin REST to platform-namespace pods only.
3. Postgres is not reachable from outside the cluster.
4. OTel Collector blocks token/key/password patterns before export.

If any assumption is violated, the mitigations in this threat model may not hold. Assumption violations must be treated as P1 security incidents.

## Mitigation Tracking

| Domain | Mitigation file | Open threats | Mitigated threats |
|--------|-----------------|-------------|------------------|
| Authentication & Identity | [mitigations/auth-identity.md](mitigations/auth-identity.md) | 0 | 5 |
| Data Integrity | [mitigations/data-integrity.md](mitigations/data-integrity.md) | 1 | 4 |
| Key Management | [mitigations/key-management.md](mitigations/key-management.md) | 0 | 5 |

**Total open threats**: 1 (T-DI-02 in data-integrity: ODRL policy payload injection — status: `Open`, mitigation in progress).

## Adding New Threats

When a new threat is identified (through security review, incident analysis, or architecture change):

1. Classify using STRIDE
2. Assign a threat ID: `T-{domain-abbreviation}-{sequence}` (e.g., `T-AI-06`)
3. Add to the relevant mitigation file
4. Add to the Threat Dragon JSON model
5. If the threat is `Open`: create a backlog ticket and add it to `docs/arc42/11-risks-and-technical-debt.md`
6. If the threat is `Mitigated`: add evidence link (test file, ADR, or infrastructure configuration)

## Tools

- **OWASP Threat Dragon** (v2.2.0): Desktop app for editing and rendering the DFD JSON models. Download from [owasp.org/www-project-threat-dragon](https://owasp.org/www-project-threat-dragon/).
- **STRIDE classification**: Used for all threats in this model. See [Glossary: STRIDE](../glossary.md).
- **Evidence links**: Point to test files in `tests/crypto-boundaries/`, `tests/tenancy/`, or infrastructure configuration in `infra/`.
- **Rendered diagrams**: committed placeholders live under `threat-model/rendered/`;
  CI and local review flows may refresh them from the Threat Dragon source.
