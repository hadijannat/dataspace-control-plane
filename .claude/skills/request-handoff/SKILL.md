---
name: request-handoff
description: Generate a pre-filled handoff template for a directory and instruct the teammate to write it.
---
# Request Handoff

## Steps

1. **Take directory name as argument.**
   Accept one argument: the directory name (e.g., `core`, `adapters`, `procedures`).
   If not provided, ask: "Which directory are you writing a handoff for?"

   Valid directories: `core`, `schemas`, `adapters`, `procedures`, `apps`, `packs`,
   `tests`, `infra`, `docs`.

2. **Read existing handoff if present.**
   Check if `.claude/handoffs/<dir>.md` exists. If so, read it and use its existing
   content as a starting point so the teammate can update rather than rewrite.

3. **Output the pre-filled handoff template.**
   Using the format from `.claude/handoffs/README.md`, emit a template with:
   - Header filled with directory name and today's date
   - "Scope Completed" pre-populated from recent git diff for the directory
     (`git diff --name-only HEAD -- <dir>/` gives changed files as a hint)
   - "Files Changed" pre-populated from the same git diff
   - "Verification Run" section with the correct commands for the directory
   - Remaining sections left as fill-in prompts

   Correct verification commands per directory:
   - `core`: `find core -maxdepth 2 -type d | sort` + `make test-core` + `pytest tests/unit -k core`
   - `schemas`: `find schemas -maxdepth 2 -type d | sort` + `make test-schemas`
   - `adapters`: `find adapters -maxdepth 3 -type d | sort` + `make test-adapters` + `pytest tests/integration -k adapters`
   - `procedures`: `find procedures -maxdepth 2 -type d | sort` + `make test-procedures` + `pytest tests/integration -k procedures`
   - `apps`: `make test-apps` + `pytest tests/integration -k apps`
   - `packs`: `find packs -maxdepth 2 -type d | sort` + `make test-packs`
   - `tests`: `pytest` + `pytest tests/compatibility/dsp-tck` + `pytest tests/tenancy`
   - `infra`: `find infra -maxdepth 2 -type d | sort` + `terraform validate` + `helm lint infra/helm`
   - `docs`: `find docs -maxdepth 2 -type d | sort` + `markdownlint docs`

4. **Instruct the teammate.**
   Tell them:
   - Fill in every section of the template
   - Write the completed handoff to `.claude/handoffs/<dir>.md`
   - The `TeammateIdle` and `TaskCompleted` hooks will check for this file
   - The "Downstream Impact" section is the most important for cross-boundary coordination
