---
title: "OpenAPI Reference"
summary: "Source, bundled, and generated API artifacts for the control-api OpenAPI 3.1 contract, including the export and bundle workflow."
owner: docs-lead
last_reviewed: "2026-03-16"
status: approved
---

The control-api OpenAPI artifacts are managed as three layers:

```text
docs/api/openapi/
├── export_control_api.py
├── source/
│   └── control-api.yaml
├── bundled/
│   └── control-api.yaml
└── generated/
    └── .gitkeep
```

## Source Artifact

`source/control-api.yaml` is the committed OpenAPI 3.1 export from the FastAPI
application.

Refresh it with:

```bash
python docs/api/openapi/export_control_api.py
```

The export script bootstraps a docs-safe environment so the app can be imported
without production secrets.

## Bundled Artifact

`bundled/control-api.yaml` is the committed Redocly bundle used for review,
linting, and downstream reference generation.

Refresh it with:

```bash
pnpm --dir docs exec redocly bundle api/openapi/source/control-api.yaml \
  --output api/openapi/bundled/control-api.yaml
```

## Generated Outputs

`generated/` is reserved for CI-only rendered outputs such as ReDoc HTML. Those
artifacts are not committed.

## Verification Commands

```bash
pnpm --dir docs exec redocly lint api/openapi/source/control-api.yaml
pnpm --dir docs exec redocly bundle api/openapi/source/control-api.yaml \
  --output /tmp/control-api.bundled.yaml
diff -u /tmp/control-api.bundled.yaml docs/api/openapi/bundled/control-api.yaml
```

The docs pytest suite also compares the committed source spec against a fresh
export from the live FastAPI app to catch drift.
