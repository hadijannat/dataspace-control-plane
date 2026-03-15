#!/usr/bin/env python3
"""
tests/scripts/collect_artifacts.py
Collect test evidence artifacts into a single output directory.

Copies:
  - Playwright traces from tests/e2e/artifacts/
  - coverage.xml from working directory
  - JUnit XML from tests/compatibility/*/reports/

Prints a manifest of collected artifacts.

Usage:
    python tests/scripts/collect_artifacts.py --output-dir /tmp/artifacts
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def collect(output_dir: Path, repo_root: Path) -> list[str]:
    """Copy artifacts to output_dir and return manifest lines."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[str] = []

    # ---- Playwright traces ------------------------------------------------
    playwright_src = repo_root / "tests" / "e2e" / "artifacts"
    if playwright_src.exists():
        for trace in playwright_src.rglob("*.zip"):
            dest = output_dir / "playwright" / trace.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(trace, dest)
            manifest.append(f"playwright/{trace.name}")
        for screenshot in playwright_src.rglob("*.png"):
            dest = output_dir / "playwright" / screenshot.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(screenshot, dest)
            manifest.append(f"playwright/{screenshot.name}")

    # ---- coverage.xml ----------------------------------------------------
    coverage_src = repo_root / "coverage.xml"
    if coverage_src.exists():
        dest = output_dir / "coverage.xml"
        shutil.copy2(coverage_src, dest)
        manifest.append("coverage.xml")
    else:
        # Check common locations
        for candidate in [
            repo_root / "tests" / "coverage.xml",
            Path.cwd() / "coverage.xml",
        ]:
            if candidate.exists():
                dest = output_dir / "coverage.xml"
                shutil.copy2(candidate, dest)
                manifest.append("coverage.xml")
                break

    # ---- TCK JUnit XML ---------------------------------------------------
    compat_dir = repo_root / "tests" / "compatibility"
    if compat_dir.exists():
        for xml_file in compat_dir.rglob("reports/*.xml"):
            # Preserve structure: dsp-tck/reports/report.xml → tck/dsp-tck/report.xml
            relative = xml_file.relative_to(compat_dir)
            dest = output_dir / "tck" / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(xml_file, dest)
            manifest.append(f"tck/{relative}")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where artifacts are collected",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
        help="Repository root (default: auto-detected)",
    )
    args = parser.parse_args()

    manifest = collect(args.output_dir.resolve(), args.repo_root.resolve())

    if manifest:
        print(f"\nArtifacts collected to {args.output_dir}:")
        for entry in manifest:
            print(f"  {entry}")
        print(f"\nTotal: {len(manifest)} artifact(s)")
    else:
        print("No artifacts found to collect.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
