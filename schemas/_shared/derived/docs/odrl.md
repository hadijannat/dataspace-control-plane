# Schema Family: `odrl`

> Base ODRL policy schemas — permissions, prohibitions, obligations, constraints — plus an internal compact AST for non-graph runtime use.

**Family version:** 1.0.0  
**Validation dialect:** `https://json-schema.org/draft/2020-12/schema`  
**Effective from:** 2026-03-14  

## Upstream Standards

- **W3C ODRL Information Model 2.2** 2.2  
  https://www.w3.org/TR/odrl-model/
- **W3C ODRL Vocabulary 2.2** 2.2  
  https://www.w3.org/TR/odrl-vocab/
- **Catena-X ODRL Policy Profile 24.05** 24.05  
  https://w3id.org/catenax/policy/v1

## Local Source Schemas

## Published Bundles

- `bundles/canonical-policy-ast.bundle.schema.json`
- `bundles/constraint.bundle.schema.json`
- `bundles/duty.bundle.schema.json`
- `bundles/obligation.bundle.schema.json`
- `bundles/parse-report.bundle.schema.json`
- `bundles/permission.bundle.schema.json`
- `bundles/policy-agreement.bundle.schema.json`
- `bundles/policy-offer.bundle.schema.json`
- `bundles/policy-set.bundle.schema.json`
- `bundles/prohibition.bundle.schema.json`

| File | Title | Description |
|------|-------|-------------|
| `source/ast/canonical-policy-ast.schema.json` | Canonical Policy AST | Compact, non-graph internal representation of an ODRL policy for runtime evaluation by core/ and pac |
| `source/ast/parse-report.schema.json` | Policy Parse Report | Result of parsing an ODRL document into the canonical AST. Records both the successful AST output an |
| `source/base/constraint.schema.json` | ODRL Constraint | An ODRL Constraint — a boolean expression over operand, operator, and rightOperand/rightOperandRefer |
| `source/base/duty.schema.json` | ODRL Duty | An ODRL Duty — an action that must be performed as a consequence of a permission (pre-condition or p |
| `source/base/obligation.schema.json` | ODRL Obligation | Obligation shares the same shape as Duty but is declared at policy level rather than as a consequenc |
| `source/base/permission.schema.json` | ODRL Permission | An ODRL Permission — grants the assignee the right to perform an action on an asset, subject to opti |
| `source/base/policy-agreement.schema.json` | ODRL Policy Agreement | An ODRL Policy Agreement — a bilateral contract between assigner and assignee accepting specific per |
| `source/base/policy-offer.schema.json` | ODRL Policy Offer | An ODRL Policy Offer — a unilateral proposal from an assigner granting or denying usage rights for a |
| `source/base/policy-set.schema.json` | ODRL Policy Set | An ODRL Policy Set — a collection of policy documents with a common uid and no mandatory assigner/as |
| `source/base/prohibition.schema.json` | ODRL Prohibition | An ODRL Prohibition — denies the assignee the right to perform an action on an asset. |

## CI Gates

    python schemas/tools/validate.py --family odrl
    python schemas/tools/pin_upstream.py --dry-run --family odrl
    pytest tests/unit -k odrl_schemas

---
*Generated 2026-03-15 by `schemas/tools/generate_docs.py`*
