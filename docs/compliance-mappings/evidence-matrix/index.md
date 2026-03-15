---
title: "Evidence Matrix"
summary: "Maps each regulatory obligation to the evidence artifact produced, the schema it must conform to, and where it is stored."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Evidence Matrix

The evidence matrix maps each regulatory obligation to the evidence artifact the platform produces when satisfying it, the JSON Schema 2020-12 schema the artifact must conform to, and where the artifact is stored. This matrix is the primary reference for auditors verifying platform compliance.

## Evidence Matrix Table

| Obligation | Regulation | Evidence type | Schema | Storage location |
|-----------|-----------|--------------|--------|-----------------|
| DPP created and submitted to EU registry | ESPR 2024/1781 Art. 9 | `dpp.registry-envelope` — contains registry submission confirmation, timestamp, and registry ID | `schemas/dpp/source/exports/registry-envelope.schema.json` | DPP registry (authoritative) + Postgres `evidence_records` (backup) |
| Battery Annex XIII fields published | Battery Reg 2023/1542 Annex XIII | `dpp.evidence-envelope` — contains field completeness assertion, Annex XIII tier coverage, and BattID | `schemas/dpp/source/exports/evidence-envelope.schema.json` | Postgres `evidence_records` (append-only) + Kafka `dpp-evidence` topic |
| ODRL contract agreement signed | Catena-X Operating Model 4.0 | `odrl.policy-agreement` — contains signed ODRL policy, both party identifiers, agreement ID, and timestamp | `schemas/odrl/source/base/policy-agreement.schema.json` | Temporal workflow history (immutable) + Postgres `agreements` table |
| W3C Verifiable Credential issued | DCP protocol (Catena-X) | `vc.credential-envelope` — contains the full W3C VC 2.0 document with Data Integrity proof | `schemas/vc/source/envelope/credential-envelope.schema.json` | VC registry (external Catena-X CA) + Postgres `credentials` table (local copy) |
| Data usage metered against active agreement | Catena-X contract obligation | `metering.usage-record` — contains agreement ID, asset ID, event type, timestamp, bytes transferred | `schemas/metering/source/business/usage-record.schema.json` | Kafka `metering-events` topic (primary) + settlement service (aggregated) |
| Vault Transit signing key rotation executed | Internal SOC2 control / security policy | Vault audit log entry — contains key name, old version, new version, operator identity, timestamp | N/A — Vault native audit format | Vault audit backend → SIEM (external) |
| DPP lifecycle state transition (draft → published) | ESPR 2024/1781 Art. 9 + Battery Reg 2023/1542 | `dpp.evidence-envelope` with lifecycle event type | `schemas/dpp/source/exports/evidence-envelope.schema.json` | Postgres `evidence_records` (append-only) |
| Company onboarding completed | Catena-X Operating Model + internal | `vc.credential-envelope` (DataspaceParticipantCredential) + Postgres company record | `schemas/vc/source/envelope/credential-envelope.schema.json` | Postgres `companies` + VC registry |

## Evidence Signing

All evidence envelopes stored in Postgres are cryptographically signed via Vault Transit before persistence. The signature is embedded in the `proof` field of the envelope:

```json
{
  "type": "DataIntegrityProof",
  "cryptosuite": "ecdsa-sd-2023",
  "created": "2026-03-14T12:34:56Z",
  "verificationMethod": "did:web:api.your-org.internal#signing-key-v2",
  "proofValue": "z3tBKA2Kk..."
}
```

The `verificationMethod` field references the Vault Transit key version used for signing. Verifiers can retrieve the public key from Vault's JWKS endpoint without requiring access to the private key material.

## Evidence Immutability

Evidence records in Postgres are stored in the `evidence_records` table with the following constraints:
- The `dataspace_app` Postgres role has `INSERT` and `SELECT` grants only — no `UPDATE` or `DELETE`
- The table has a `CHECK` constraint preventing `updated_at` from being set (records have no update lifecycle)
- Periodic integrity checks in `tests/crypto-boundaries/test_no_evidence_update.py` verify that no UPDATE grants have been granted

## Querying Evidence for Audit

To retrieve all evidence for a specific passport:

```sql
-- Must be executed with the correct tenant context
SET LOCAL app.tenant_id = 'tenant-BPNL000000000001';

SELECT
    er.evidence_id,
    er.event_type,
    er.entity_id,
    er.entity_type,
    er.signed_at,
    er.proof_verification_method,
    er.payload_hash
FROM evidence_records er
WHERE er.entity_id = '<passport_id>'
    AND er.tenant_id = current_setting('app.tenant_id')
ORDER BY er.signed_at ASC;
```

To retrieve all Kafka-published metering events for an agreement:

```bash
# Kafka CLI (from within the cluster)
kafka-console-consumer.sh \
  --bootstrap-server kafka.dataspace-infra.svc.cluster.local:9092 \
  --topic metering-events \
  --from-beginning \
  --property print.headers=true | \
  grep '"agreementId":"<agreement-id>"'
```
