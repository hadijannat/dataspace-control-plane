---
title: "Guidebook Template"
summary: "Template for creating new directory guidebooks in docs/agents/."
owner: docs-lead
last_reviewed: "2026-03-16"
status: draft
---
## Purpose

- State the mission of the directory and the layer it represents in the repo architecture.

## Scope

- Describe the kinds of work this owner handles and what problems belong elsewhere.

## Owned Paths

- List the exact repo paths owned by this agent.

## Non-Owned Paths

- List neighboring roots or subtrees this agent must not edit without explicit scope.

## Read-First Files

- List the local `AGENTS.md`, this guidebook, upstream architecture docs, and any critical contracts.

## Architecture Invariants

- Capture the layer rules this directory must preserve.

## Subdirectory Map

- Enumerate each significant subdirectory and its responsibility.

## Build Order

- Give the expected implementation sequence inside the directory.

## Required Interfaces/Dependencies

- Name the allowed upstream and downstream dependencies and how they are used.

## Verification

- List existing checks first.
- Mark future commands with `Expected command once scaffolded: ...`.

## Common Failure Modes

- Call out the mistakes that most often violate boundaries or create hidden coupling.

## Handoff Contract

- Define what the owner must summarize for a lead or neighboring owner.

## Change Checklist

- Confirm boundaries preserved.
- Confirm verification run.
- Confirm docs updated.
- Confirm dependency notes recorded.
