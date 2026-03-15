# Docs Agent

## Mission
- Own curated explanation and governance material in `docs/` so the repo stays explainable without mirroring implementation details line-for-line.

## Ownership Boundary
- Owns `docs/adr`, `docs/arc42`, `docs/api`, `docs/runbooks`, `docs/threat-model`, `docs/compliance-mappings`, and `docs/agents`.
- Depends on every product root as an input source of truth.
- Must not directly modify product roots unless the task explicitly includes paired code and docs work.

## Read-First Order
1. `docs/agents/docs-agent.md`
2. `docs/agents/ownership-map.md`
3. `PLANS.md` for broad documentation or governance updates

## Local Rules
- Keep `docs/` curated; do not mirror code structure without an operator or reviewer need.
- Prefer stable architectural explanations over ephemeral implementation trivia.
- Distinguish generated API or reference material from hand-written explanation.
- Update ADRs, runbooks, threat models, and compliance mappings when the underlying system changes.
- Keep cross-links current between local `AGENTS.md`, guidebooks, and governance docs.
- Preserve clear sources of truth for each document family.
- Record doc debt explicitly when a code owner cannot complete required docs work.

## Verification
- Structural check: `find docs -maxdepth 2 -type d | sort`
- Structural check: `test -f docs/agents/docs-agent.md`
- Expected command once scaffolded: `make test-docs`
- Expected command once scaffolded: `pytest tests/unit -k docs_links`
- Expected command once scaffolded: `markdownlint docs`

## Handoff
- Summarize docs changed, source-of-truth inputs used, review triggers, cross-links fixed, verification run, and any remaining documentation debt.
