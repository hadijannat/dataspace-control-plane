# Orchestration Guide

## Purpose
- Use this guide when a lead or orchestrator is splitting a task across directory owners. The goal is clean ownership, non-overlapping edits, and explicit synthesis at the end.

## Safe Single-Owner Tasks
- The task changes files in one top-level root only.
- The task uses existing interfaces from neighboring directories.
- The task does not require new contracts, new ports, or new deployment assumptions outside the owned root.
- The task can be verified with one directory's local checks plus existing repo-wide tests.

## Cross-Cutting Tasks
- The task introduces or changes interfaces between two roots.
- The task changes a trust, tenancy, compliance, or audit boundary.
- The task changes workflow contracts between `procedures/` and `apps/temporal-workers`.
- The task changes canonical models and therefore affects adapters, procedures, tests, or docs.
- The task changes packs, schemas, or compatibility expectations across ecosystems.

## Assignment Rules
1. Split work by top-level root, not by file type.
2. Give each specialist one owned write surface.
3. Provide dependency notes instead of overlapping edit rights when possible.
4. Escalate to a shared plan in `PLANS.md` format when the task changes more than one owner boundary.

## Handoff Rules
- Every specialist handoff must include:
  - owned scope completed
  - files changed
  - verification run
  - docs updated
  - blockers
  - explicit follow-up required from neighboring owners
- The lead synthesizes handoffs into the final change summary and resolves ordering across roots.

## Why Overlapping Edits Are Forbidden
- Overlapping edits create hidden coupling and review ambiguity.
- This repo separates meaning, orchestration, integration, overlays, schemas, runtime surfaces, verification, delivery, and explanation. Crossing those boundaries ad hoc makes later automation and review unreliable.
- A specialist should leave a crisp dependency note rather than partially editing another owner's layer with incomplete context.

## Planning Expectations
- Use `PLANS.md` for multi-hour tasks, major refactors, or any task touching architecture boundaries.
- The plan should name each directory owner involved, its local objective, its verification, and the synthesis point where the lead integrates the work.
