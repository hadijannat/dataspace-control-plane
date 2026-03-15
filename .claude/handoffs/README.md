# Handoff Protocol

Each directory owner must write a handoff file to `.claude/handoffs/<dir>.md` before going idle
or completing a task. Hooks enforce this requirement.

## Why Handoffs Matter

The 9-layer ownership model keeps boundaries clean, but integration happens between waves.
A handoff artifact is the only durable record of: what changed, what was verified, what
downstream owners must follow up on, and what blockers remain. Without it, the lead
cannot safely integrate the wave or kick off the next one.

## Handoff File Naming

| Directory owner | Handoff file |
|-----------------|-------------|
| core-lead | `.claude/handoffs/core.md` |
| schemas-lead | `.claude/handoffs/schemas.md` |
| adapters-lead | `.claude/handoffs/adapters.md` |
| procedures-lead | `.claude/handoffs/procedures.md` |
| apps-lead | `.claude/handoffs/apps.md` |
| packs-lead | `.claude/handoffs/packs.md` |
| tests-lead | `.claude/handoffs/tests.md` |
| infra-lead | `.claude/handoffs/infra.md` |
| docs-lead | `.claude/handoffs/docs.md` |

## Template

Copy-paste this template and fill in each section:

```markdown
# Handoff: <directory> — Wave <N>

**Date:** YYYY-MM-DD
**Teammate:** <agent name>
**Wave:** <wave-0 | wave-1 | wave-2 | wave-3>

## Scope Completed
<!-- What was done. Be specific about files, modules, or subsystems. -->

## Files Changed
<!-- List changed files or directories. -->
- `path/to/file.py` — reason

## Verification Run
<!-- Commands executed and their outcome. -->
```
find <dir> -maxdepth 2 -type d | sort    ✓
make test-<dir>                          ✓ / ✗ (note failures)
pytest tests/unit -k <dir>               ✓ / ✗
```

## Design / Contract Changes
<!-- Any interface, port, schema, or workflow contract that changed. -->
<!-- Downstream owners MUST read this section. -->

## Downstream Impact
<!-- Which directories must follow up and why. -->
- `<dir>/` — needs to ...

## Blockers and Open Questions
<!-- Anything that could not be resolved. Include cross-boundary notes. -->

## Recommended Next Tasks
<!-- For the lead or next wave teammates. -->
```

## Protocol Rules

1. **Write before idle**: The `TeammateIdle` hook blocks going idle without a handoff file.
2. **Write before task completion**: The `TaskCompleted` hook checks for the handoff.
3. **Use `/request-handoff <dir>`**: This skill auto-fills the template from your context.
4. **Lead reads all handoffs** before running `/integrate-wave` or `/close-wave`.
5. **Archive, don't delete**: Handoff files accumulate across waves. The lead appends or creates
   new wave-scoped files; do not overwrite previous waves without archiving.
6. **Cross-boundary notes go here**: If you needed something from another directory, record
   the dependency in your handoff. Never silently cross the boundary.
