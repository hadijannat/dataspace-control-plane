---
title: "[short noun phrase describing the decision]"
summary: "Template for new MADR-style architecture decision records."
owner: docs-lead
last_reviewed: "2026-03-16"
status: proposed
date: YYYY-MM-DD
decision-makers:
  - "[name or role of primary decision-maker]"
consulted:
  - "[name or role of SME consulted before decision]"
informed:
  - "[name or role of stakeholder informed after decision]"
---

## Context and Problem Statement

[Describe the problem or context that requires a decision. Be specific about the forces at play: What is the platform trying to do? What constraints apply? What will happen if no decision is made?]

[2-4 paragraphs is usually sufficient. Avoid justifying the chosen option here — that belongs in Decision Outcome.]

## Decision Drivers

* [Force 1: a specific quality goal, constraint, or capability requirement that the decision must satisfy]
* [Force 2: another force]
* [Force 3: another force]
* [Add more as needed — be specific. "Performance" is not a decision driver. "P95 signing latency < 100ms under 50 concurrent signing operations" is.]

## Considered Options

* [Option 1 — name only here; details in Pros and Cons section below]
* [Option 2]
* [Option 3]
* [Add more as needed]

## Decision Outcome

**Chosen option: "[Option N]"**, because [concise justification — explain which decision drivers are satisfied and why this option satisfies them better than the alternatives].

### Positive Consequences

* [Benefit 1: what does this decision enable or make easier?]
* [Benefit 2]
* [Add more as needed]

### Negative Consequences

* [Drawback 1: what does this decision make harder, more complex, or more expensive?]
* [Drawback 2]
* [Add more as needed]

### Confirmation

[Optional but recommended: How can we verify that this decision was implemented correctly? Name a specific test file, CI gate, or observable behavior that confirms the decision is in effect.]

Examples:

* `tests/crypto-boundaries/vault_transit/test_no_key_export.py` must pass
* `mkdocs build --strict` must succeed with no warnings
* `tests/compatibility/dsp-tck` suite must pass in staging

## Pros and Cons of the Options

### [Option 1]

[Brief description of the option — 1-3 sentences.]

* Good, because [specific benefit]
* Good, because [specific benefit]
* Bad, because [specific drawback]
* Bad, because [specific drawback]

### [Option 2]

[Brief description.]

* Good, because [benefit]
* Bad, because [drawback]

### [Option 3]

[Brief description.]

* Good, because [benefit]
* Bad, because [drawback]

---

<!-- Instructions: remove this comment block before submitting.
- Set status to "proposed" when first creating. Change to "accepted" after team review.
- Date should be the date the decision was made (or proposed), not today's date.
- Decision-makers: list the leads who had authority to make this decision.
- Consulted: list SMEs whose input was sought before the decision.
- Informed: list stakeholders who need to know about the decision but did not participate.
- Link this ADR from docs/adr/index.md and docs/arc42/09-architecture-decisions.md.
-->
