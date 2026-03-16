---
title: "Agent Guidebooks"
summary: "Index of the durable guidebooks that define directory-specific ownership and execution rules."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---
## Purpose

- `AGENTS.md` files are the short routing layer. They tell Codex which directory it owns, what it may touch, and which verification steps to run.
- Files in `docs/agents/` are the deep playbooks. They hold the durable architecture rules, subdirectory responsibilities, handoff contracts, and directory-specific implementation order that would otherwise make `AGENTS.md` too large.

## Guidebooks

- [`apps-agent.md`](apps-agent.md)
- [`core-agent.md`](core-agent.md)
- [`procedures-agent.md`](procedures-agent.md)
- [`adapters-agent.md`](adapters-agent.md)
- [`packs-agent.md`](packs-agent.md)
- [`schemas-agent.md`](schemas-agent.md)
- [`tests-agent.md`](tests-agent.md)
- [`infra-agent.md`](infra-agent.md)
- [`docs-agent.md`](docs-agent.md)

## Shared Governance

- [`ownership-map.md`](ownership-map.md) defines boundaries, dependencies, forbidden edit zones, and required handoff outputs.
- [`orchestration-guide.md`](orchestration-guide.md) explains how a lead agent should split work across owners and when cross-directory work must be escalated.
- [`_template.md`](_template.md) is the canonical template for future directory guidebooks.
- `PLANS.md` defines how to write execution plans for large or cross-directory work.
- `.agents/skills/` contains repo-local reusable workflows.

## How To Use This Layer

1. Read the nearest `AGENTS.md`.
2. Open the matching guidebook here before editing.
3. Use `ownership-map.md` when a task may cross directory boundaries.
4. Use `PLANS.md` when the change spans multiple owners, takes hours, or changes architecture.
