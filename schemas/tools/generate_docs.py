#!/usr/bin/env python3
"""
schemas/tools/generate_docs.py
Render minimal human-readable Markdown documentation from manifest.yaml files
and schema $id / title / description fields.

Usage:
    python schemas/tools/generate_docs.py [--family FAMILY] [--out-dir OUT_DIR]

Output:
    One Markdown file per schema family in OUT_DIR (default: docs/schemas/).

Exit codes:
    0  Documentation generated.
    1  Error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import date

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required.  Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SCHEMAS_ROOT.parent
DEFAULT_OUT = SCHEMAS_ROOT / "_shared" / "derived" / "docs"
FAMILIES = ["vc", "odrl", "aas", "dpp", "metering", "enterprise-mapping"]


def _load_manifest(family_dir: Path) -> dict | None:
    manifest_path = family_dir / "manifest.yaml"
    if not manifest_path.exists():
        return None
    with open(manifest_path) as f:
        return yaml.safe_load(f)


def _schema_summary(schema_path: Path) -> dict:
    try:
        with open(schema_path) as f:
            s = json.load(f)
        return {
            "id": s.get("$id", ""),
            "title": s.get("title", schema_path.stem),
            "description": s.get("description", ""),
            "dialect": s.get("$schema", ""),
            "source_standard": s.get("x-source-standard"),
            "source_version": s.get("x-source-version"),
        }
    except (json.JSONDecodeError, OSError):
        return {"id": "", "title": schema_path.stem, "description": "", "dialect": ""}


def _render_family(family: str, family_dir: Path) -> str:
    lines: list[str] = []
    manifest = _load_manifest(family_dir)

    lines.append(f"# Schema Family: `{family}`")
    lines.append("")
    if manifest:
        lines.append(f"> {manifest.get('description', '')}")
        lines.append("")
        lines.append(f"**Family version:** {manifest.get('version', 'n/a')}  ")
        lines.append(f"**Validation dialect:** `{manifest.get('validation_dialect', 'n/a')}`  ")
        lines.append(f"**Effective from:** {manifest.get('effective_from', 'n/a')}  ")
        lines.append("")

        standards = manifest.get("upstream_standards", [])
        if standards:
            lines.append("## Upstream Standards")
            lines.append("")
            for std in standards:
                lines.append(f"- **{std['name']}** {std['version']}  ")
                lines.append(f"  {std['source_uri']}")
            lines.append("")

    # Local source schemas
    source_schemas = sorted((family_dir / "source").rglob("*.schema.json")) \
        if (family_dir / "source").exists() else []

    if source_schemas:
        lines.append("## Local Source Schemas")
        lines.append("")

    bundle_schemas = sorted((family_dir / "bundles").glob("*.schema.json")) \
        if (family_dir / "bundles").exists() else []
    if bundle_schemas:
        lines.append("## Published Bundles")
        lines.append("")
        for bp in bundle_schemas:
            lines.append(f"- `{bp.relative_to(family_dir)}`")
        lines.append("")
        lines.append("| File | Title | Description |")
        lines.append("|------|-------|-------------|")
        for sp in source_schemas:
            summary = _schema_summary(sp)
            rel = sp.relative_to(family_dir)
            desc = summary["description"].replace("|", "\\|").replace("\n", " ")[:100]
            lines.append(f"| `{rel}` | {summary['title']} | {desc} |")
        lines.append("")

    # Examples
    valid_ex = sorted((family_dir / "examples" / "valid").glob("*.json")) \
        if (family_dir / "examples" / "valid").exists() else []
    invalid_ex = sorted((family_dir / "examples" / "invalid").glob("*.json")) \
        if (family_dir / "examples" / "invalid").exists() else []

    if valid_ex or invalid_ex:
        lines.append("## Examples")
        lines.append("")
        if valid_ex:
            lines.append(f"**Valid:** {', '.join(f'`{e.name}`' for e in valid_ex)}")
        if invalid_ex:
            lines.append(f"**Invalid:** {', '.join(f'`{e.name}`' for e in invalid_ex)}")
        lines.append("")

    # CI gates
    if manifest and manifest.get("ci_gates"):
        lines.append("## CI Gates")
        lines.append("")
        for gate in manifest["ci_gates"]:
            lines.append(f"    {gate}")
        lines.append("")

    lines.append(f"---\n*Generated {date.today().isoformat()} by `schemas/tools/generate_docs.py`*")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--family", help="Limit to one family.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help=f"Output directory (default: {DEFAULT_OUT})")
    args = parser.parse_args(argv)

    families = [args.family] if args.family else FAMILIES

    # SECURITY: --out-dir must stay inside SCHEMAS_ROOT.
    try:
        args.out_dir.resolve().relative_to(SCHEMAS_ROOT.resolve())
    except ValueError:
        print(
            f"ERROR: --out-dir must be inside SCHEMAS_ROOT ({SCHEMAS_ROOT}): {args.out_dir}",
            file=sys.stderr,
        )
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)

    errors = 0
    for family in families:
        family_dir = SCHEMAS_ROOT / family
        if not family_dir.exists():
            print(f"  SKIP {family}: directory not found", file=sys.stderr)
            continue
        try:
            content = _render_family(family, family_dir)
            out = args.out_dir / f"{family}.md"
            out.write_text(content)
            try:
                rel = out.relative_to(REPO_ROOT)
            except ValueError:
                rel = out
            print(f"  OK   {rel}")
        except Exception as exc:
            print(f"  FAIL {family}: {exc}", file=sys.stderr)
            errors += 1

    # Generate index
    index_lines = [
        "# Schema Families Index",
        "",
        "| Family | Description |",
        "|--------|-------------|",
    ]
    for family in families:
        family_dir = SCHEMAS_ROOT / family
        m = _load_manifest(family_dir) if family_dir.exists() else None
        desc = m.get("description", "") if m else ""
        index_lines.append(f"| [`{family}`]({family}.md) | {desc} |")
    index_lines.append(f"\n---\n*Generated {date.today().isoformat()}*")
    (args.out_dir / "index.md").write_text("\n".join(index_lines) + "\n")
    index_path = args.out_dir / "index.md"
    try:
        rel = index_path.relative_to(REPO_ROOT)
    except ValueError:
        rel = index_path
    print(f"  OK   {rel}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
