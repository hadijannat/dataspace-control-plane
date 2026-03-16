---
title: "Use MkDocs + Material for docs-as-code publishing"
summary: "Architecture decision record establishing MkDocs Material as the docs-as-code publishing stack."
owner: docs-lead
last_reviewed: "2026-03-16"
status: accepted
date: 2026-03-14
decision-makers:
  - docs-lead
consulted:
  - infra-lead
  - apps-lead
  - all-leads
informed:
  - all-leads
---

## Context and Problem Statement

The `docs/` layer needs a docs-as-code publishing workflow that produces a navigable, searchable documentation site from Markdown source files stored in the repository. The site must render architecture diagrams, code examples, API references, and compliance tables without requiring authors to leave Markdown.

The platform operates in regulated environments where offline access (air-gapped installations, disconnected operator kits) is a real requirement. Client-side search that works without a backend is therefore a functional requirement, not a nice-to-have.

The documentation toolchain must be Python-based (or at least installable via Python packaging tools) to align with the repo's primary runtime stack. Adding a Node.js build dependency at the documentation layer would create a second runtime requirement in the infra build pipeline.

## Decision Drivers

* Must support client-side search that works offline (no search backend required)
* Must render Mermaid diagrams from fenced code blocks without an external rendering service
* Must support an explicit `nav:` definition in configuration so the sidebar is controlled, not auto-generated
* Must be Python-based and installable via `pip` or `uv`
* Must support syntax-highlighted code blocks across Python, YAML, JSON, Bash, SQL
* Must not require a JavaScript SSR server at runtime (static site export sufficient)
* OpenAPI reference rendering is desirable but can be handled by a separate Redocly step

## Considered Options

* MkDocs + Material theme (chosen)
* Docusaurus (React/MDX)
* Sphinx (RST-primary with MyST Markdown plugin)
* mdBook (Rust-based, Markdown)

## Decision Outcome

**Chosen option: "MkDocs + Material"**, because it satisfies all decision drivers: client-side search is built into the Material theme and works offline; Mermaid is supported natively via `pymdownx.superfences` custom fences; `nav:` in `mkdocs.yml` gives full sidebar control; `mkdocs-material` is a Python package installable with `uv add mkdocs-material`; Pygments provides syntax highlighting for all required languages. The static site output can be served from a Kubernetes ConfigMap or an S3-compatible bucket without a dynamic server.

### Positive Consequences

* Offline search: the generated `search/search_index.json` enables full-text search in the browser with no backend
* Mermaid-native: architecture diagrams are version-controlled as text and render in the browser without a screenshot step
* Python ecosystem consistency: `mkdocs-material`, `mkdocs-minify-plugin`, and `mike` (versioning) install alongside the platform's Python dependencies
* Admonitions, tabbed content, code annotations, and content tabs are all supported natively
* `mkdocs build --strict` provides a CI-enforceable correctness gate

### Negative Consequences

* No JavaScript SSR: Next.js-style server-rendered documentation (useful for personalized or role-filtered docs) is not supported by MkDocs
* No built-in OpenAPI renderer: OpenAPI reference is handled by a separate Redocly CLI step (`redocly bundle` + `redocly build-docs`); this adds a Node.js dependency to the docs CI step
* Large nav configurations (`nav:` in `mkdocs.yml`) must be kept in sync with the actual file tree — orphaned files will not appear in the site

### Confirmation

`mkdocs build --strict` must complete with zero warnings and zero errors in CI. All pages listed in `nav:` must have corresponding Markdown files; missing files cause a strict-mode failure.

## Pros and Cons of the Options

### MkDocs + Material

A Python-based static site generator with a Material Design theme that provides navigation tabs, search, code highlighting, and Mermaid support.

* Good, because offline client-side search is included
* Good, because Mermaid renders from fenced blocks via `pymdownx.superfences`
* Good, because Python-only dependency chain
* Good, because `nav:` gives full sidebar control
* Bad, because no built-in OpenAPI renderer (requires Redocly separately)
* Bad, because no SSR — dynamic content requires JavaScript-only solutions

### Docusaurus

A React and MDX-based documentation framework popular in the JavaScript/Node.js ecosystem.

* Good, because MDX enables React components in documentation (useful for interactive API explorers)
* Good, because versioning support is built in
* Bad, because requires Node.js in the build pipeline — a second runtime language dependency
* Bad, because Mermaid support requires a plugin and is less stable than MkDocs/Material's native support
* Bad, because offline search requires additional configuration

### Sphinx

The traditional Python documentation generator, RST-primary with MyST Markdown plugin.

* Good, because Python-based
* Good, because mature autodoc support for extracting API docs from Python docstrings
* Bad, because RST-first — Markdown feels like a second-class citizen despite MyST
* Bad, because Mermaid support is a third-party extension with limited maintenance
* Bad, because the Material-equivalent theme (sphinx-book-theme, furo) is less feature-rich for navigation

### mdBook

A Rust-based documentation tool popular in the Rust ecosystem.

* Good, because extremely fast builds
* Good, because simple, minimal configuration
* Bad, because Rust toolchain required in the build pipeline
* Bad, because limited plugin ecosystem for Mermaid, admonitions, and code annotations
* Bad, because `nav:` equivalent requires manual SUMMARY.md maintenance
