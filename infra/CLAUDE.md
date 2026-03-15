# infra — CLAUDE.md

## Purpose
Delivery substrate: packages releases in Helm, provisions durable shared infrastructure in Terraform, defines image builds and local composition in Docker, and manages observability telemetry assets.

## Architecture Invariants
- **`helm/` owns release packaging only:** charts, values schemas, templates, and release wiring. No business logic, no domain decisions.
- **`terraform/` owns durable shared infrastructure:** root modules, reusable modules, state boundaries, and environment composition. No application orchestration or business workflows.
- **Secrets must never be committed to git.** Use external secret stores (Vault, cloud KMS, operator-injected env) and reference by handle or secret path only.
- **Immutable image tags.** Production Helm values and Terraform modules must reference pinned digest or semantic version tags — never `latest`.

## Forbidden Shortcuts
- Do not define canonical models, procedure logic, or domain rules in Helm templates or Terraform modules.
- Do not commit secrets, private keys, or credential files in any form.
- Do not use `latest` image tags in production manifests.

## Allowed Dependencies
- `apps/` — image names, port conventions, and environment variable contracts (read only)
- `adapters/` — external service dependencies and health endpoint shapes (read only)
- `tests/` — environment definitions for integration test infrastructure (read only)
- `docs/runbooks/` — operator procedures that inform infra design (read only)

## Verification
```bash
# Structural check
find infra -maxdepth 2 -type d | sort

# Infra validation (once scaffolded)
make test-infra
terraform validate
helm lint infra/helm
```

## Required Docs Updates
When `infra/` changes:
- Update `docs/runbooks/` for any operator-visible deployment or environment changes
- Update `docs/arc42/` if environment topology or service boundaries change
- Notify `apps-lead` or `adapters-lead` if new environment variables or secrets conventions are introduced

## Handoff Protocol
Write to `.claude/handoffs/infra.md` before going idle. Required fields:
- Packaging changes (Helm chart version bumps, new charts)
- Environment changes (new resources, destroyed resources, renamed variables)
- Secrets handling impact (new external references, changed vault paths)
- Observability changes (new dashboards, alert rules, SLO definitions)
- Verification run outcome
- Runbook update needs

## Full Guidebook
`docs/agents/infra-agent.md`
