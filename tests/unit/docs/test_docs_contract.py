from __future__ import annotations

import datetime
import functools
import importlib.util
import json
import re
from pathlib import Path

import yaml
from markdown.extensions.toc import slugify_unicode


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_ROOT = REPO_ROOT / "docs"
MKDOCS_CONFIG_PATH = REPO_ROOT / "mkdocs.yml"
OPENAPI_EXPORT_PATH = DOCS_ROOT / "api" / "openapi" / "export_control_api.py"
EXCLUDED_DOC_PATH_PARTS = {"node_modules", ".git"}

EXPECTED_THREAT_DRAGON_MODELS = {
    "platform.json",
    "onboarding.json",
    "negotiation.json",
    "dpp-provisioning.json",
    "machine-trust.json",
}
REQUIRED_OSCAL_PROPS = {
    "source-standard",
    "source-version",
    "effective-date",
    "pack-reference",
}
VALID_FRONT_MATTER_STATUSES = {
    "draft",
    "proposed",
    "approved",
    "accepted",
    "deprecated",
    "superseded",
}
# Keys in mkdocs.yml that must be present for a valid site build.
REQUIRED_MKDOCS_CONFIG_KEYS = {"site_name", "docs_dir", "theme", "nav"}


_MARKDOWN_FILES: list[Path] | None = None


def iter_markdown_files() -> list[Path]:
    """Return sorted list of all published markdown files. Result is cached after first call."""
    global _MARKDOWN_FILES
    if _MARKDOWN_FILES is None:
        _MARKDOWN_FILES = sorted(
            path
            for path in DOCS_ROOT.rglob("*.md")
            if not EXCLUDED_DOC_PATH_PARTS.intersection(path.parts)
        )
    return _MARKDOWN_FILES


def split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise AssertionError("missing YAML front matter")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise AssertionError("malformed YAML front matter")
    front_matter = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return front_matter, body


def non_fenced_lines(text: str) -> list[str]:
    lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return lines


def heading_slugs_for_markdown(path: Path) -> set[str]:
    _, body = split_front_matter(path.read_text(encoding="utf-8"))
    slugs: list[str] = []
    seen: dict[str, int] = {}
    for line in non_fenced_lines(body):
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        heading = stripped.lstrip("#").strip()
        if not heading:
            continue
        slug = slugify_unicode(heading, "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        slugs.append(slug if count == 0 else f"{slug}_{count}")
    return set(slugs)


def iter_markdown_links(path: Path) -> list[str]:
    links: list[str] = []
    for line in non_fenced_lines(path.read_text(encoding="utf-8")):
        without_inline_code = re.sub(r"`[^`]*`", "", line)
        links.extend(re.findall(r"\[[^\]]+\]\(([^)]+)\)", without_inline_code))
    return links


def flatten_nav(items: list) -> list[str]:
    paths: list[str] = []
    for item in items:
        if isinstance(item, str):
            paths.append(item)
            continue
        if isinstance(item, dict):
            for value in item.values():
                if isinstance(value, str):
                    paths.append(value)
                elif isinstance(value, list):
                    paths.extend(flatten_nav(value))
    return paths


def load_mkdocs_config() -> dict:
    # yaml.Loader (full loader) is required because mkdocs.yml contains !!python/name: tags
    # for the emoji and superfences plugins. The file is repo-controlled — risk is bounded.
    return yaml.load(MKDOCS_CONFIG_PATH.read_text(encoding="utf-8"), Loader=yaml.Loader)


@functools.lru_cache(maxsize=1)
def load_openapi_export_module():
    """Import and execute the export script once; cache the module for subsequent calls."""
    spec = importlib.util.spec_from_file_location(
        "docs_api_openapi_export",
        OPENAPI_EXPORT_PATH,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_published_markdown_page_has_required_front_matter() -> None:
    required = {"title", "summary", "owner", "last_reviewed", "status"}
    for path in iter_markdown_files():
        front_matter, _ = split_front_matter(path.read_text(encoding="utf-8"))
        missing = required - set(front_matter)
        assert not missing, f"{path.relative_to(REPO_ROOT)} missing {sorted(missing)}"


def test_published_markdown_pages_do_not_define_body_h1_headings() -> None:
    for path in iter_markdown_files():
        _, body = split_front_matter(path.read_text(encoding="utf-8"))
        headings = [line.strip() for line in non_fenced_lines(body) if line.strip().startswith("# ")]
        assert not headings, f"{path.relative_to(REPO_ROOT)} contains body H1 headings: {headings}"


def test_mkdocs_nav_covers_every_markdown_page() -> None:
    config = load_mkdocs_config()
    nav_paths = {Path(item) for item in flatten_nav(config["nav"])}
    markdown_paths = {path.relative_to(DOCS_ROOT) for path in iter_markdown_files()}
    assert markdown_paths == nav_paths


def test_mkdocs_nav_entries_exist() -> None:
    config = load_mkdocs_config()
    for entry in flatten_nav(config["nav"]):
        assert (DOCS_ROOT / entry).is_file(), f"nav entry does not exist: {entry}"


def test_internal_markdown_links_and_anchors_resolve() -> None:
    for path in iter_markdown_files():
        for raw_target in iter_markdown_links(path):
            target = raw_target.split(" ", 1)[0]
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("/"):
                raise AssertionError(f"{path.relative_to(REPO_ROOT)} uses an absolute internal link: {target}")
            destination, _, anchor = target.partition("#")
            target_path = (path.parent / destination).resolve() if destination else path
            assert target_path.exists(), f"{path.relative_to(REPO_ROOT)} -> missing link target {target}"
            if anchor and target_path.suffix == ".md":
                assert anchor in heading_slugs_for_markdown(target_path), (
                    f"{path.relative_to(REPO_ROOT)} -> missing anchor {anchor} in "
                    f"{target_path.relative_to(REPO_ROOT)}"
                )


def test_adr_files_follow_numbered_filename_and_metadata_rules() -> None:
    adr_root = DOCS_ROOT / "adr"
    for path in sorted(adr_root.glob("*.md")):
        if path.name == "index.md":
            continue
        if path.name == "_template.md":
            front_matter, _ = split_front_matter(path.read_text(encoding="utf-8"))
            for key in ("date", "decision-makers", "consulted", "informed"):
                assert key in front_matter
            continue
        assert re.match(r"^\d{4}-[a-z0-9-]+\.md$", path.name), path.name
        front_matter, _ = split_front_matter(path.read_text(encoding="utf-8"))
        for key in ("date", "decision-makers", "consulted", "informed"):
            assert key in front_matter, f"{path.name} missing {key}"


def test_threat_dragon_models_exist_and_parse() -> None:
    model_root = DOCS_ROOT / "threat-model" / "threat-dragon"
    discovered = {path.name for path in model_root.glob("*.json")}
    assert discovered == EXPECTED_THREAT_DRAGON_MODELS
    for path in sorted(model_root.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["version"] == "2.2.0"
        assert data["detail"]["diagrams"], f"{path.name} must contain at least one diagram"


def test_oscal_files_have_required_metadata_and_valid_relative_hrefs() -> None:
    for path in sorted((DOCS_ROOT / "compliance-mappings" / "oscal").rglob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        top_level_key = next(iter(data))
        metadata = data[top_level_key]["metadata"]
        props = {prop["name"] for prop in metadata.get("props", [])}
        assert REQUIRED_OSCAL_PROPS.issubset(props), f"{path.name} missing required OSCAL props"

        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "href" and isinstance(child, str):
                        if child.startswith(("http://", "https://", "#")):
                            continue
                        resolved = (path.parent / child).resolve()
                        assert resolved.exists(), f"{path.relative_to(REPO_ROOT)} -> missing {child}"
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(data)


def test_openapi_source_matches_live_fastapi_export() -> None:
    export_module = load_openapi_export_module()
    live_schema = export_module.build_schema()
    committed_source = yaml.safe_load(
        (DOCS_ROOT / "api" / "openapi" / "source" / "control-api.yaml").read_text(encoding="utf-8")
    )
    assert committed_source == live_schema


def test_openapi_bundled_artifact_exists() -> None:
    bundled_path = DOCS_ROOT / "api" / "openapi" / "bundled" / "control-api.yaml"
    assert bundled_path.is_file()
    bundled = yaml.safe_load(bundled_path.read_text(encoding="utf-8"))
    assert bundled["openapi"] == "3.1.0"


def test_openapi_bundled_artifact_matches_source() -> None:
    """Guard against the bundled artifact silently diverging from the source spec.

    The Makefile enforces this with ``redocly bundle ... && diff``, but that
    path is only exercised by ``make test-docs``.  This test makes the same
    invariant catchable via a plain ``pytest tests/unit/docs`` run.

    Because the repo currently does not use ``$ref`` composition across
    multiple source files, source and bundled must be identical in content.
    If ref-composition is introduced, this test should be updated to compare
    the resolved structures rather than raw dicts.
    """
    source = yaml.safe_load(
        (DOCS_ROOT / "api" / "openapi" / "source" / "control-api.yaml").read_text(encoding="utf-8")
    )
    bundled = yaml.safe_load(
        (DOCS_ROOT / "api" / "openapi" / "bundled" / "control-api.yaml").read_text(encoding="utf-8")
    )
    assert source == bundled, (
        "docs/api/openapi/bundled/control-api.yaml is out of sync with "
        "docs/api/openapi/source/control-api.yaml.  "
        "Regenerate the bundled artifact with: "
        "pnpm --dir docs exec redocly bundle api/openapi/source/control-api.yaml "
        "--output docs/api/openapi/bundled/control-api.yaml"
    )


def test_mkdocs_config_has_required_top_level_keys() -> None:
    """Verify that mkdocs.yml contains all keys required for a valid site build.

    Missing any of these keys causes ``mkdocs build`` to abort.  Catching the
    absence at pytest time gives a faster, more descriptive failure than waiting
    for the full build step in CI.
    """
    config = load_mkdocs_config()
    missing = REQUIRED_MKDOCS_CONFIG_KEYS - set(config)
    assert not missing, f"mkdocs.yml is missing required keys: {sorted(missing)}"


def test_mkdocs_docs_dir_exists() -> None:
    """Verify that the docs_dir declared in mkdocs.yml is a real directory."""
    config = load_mkdocs_config()
    docs_dir = REPO_ROOT / config["docs_dir"]
    assert docs_dir.is_dir(), (
        f"mkdocs.yml docs_dir '{config['docs_dir']}' does not exist as a directory "
        f"relative to repo root"
    )


def test_front_matter_status_uses_allowed_values() -> None:
    """Reject any status value that falls outside the controlled vocabulary.

    An unrecognised status (e.g., a typo or a new value not added to the
    allowed set) indicates the field is being used inconsistently.  The test
    skips ``_template.md`` files because templates intentionally use
    placeholder values.
    """
    for path in iter_markdown_files():
        if path.name.startswith("_"):
            continue
        front_matter, _ = split_front_matter(path.read_text(encoding="utf-8"))
        status = front_matter.get("status", "")
        assert status in VALID_FRONT_MATTER_STATUSES, (
            f"{path.relative_to(REPO_ROOT)}: invalid status {status!r}. "
            f"Allowed values: {sorted(VALID_FRONT_MATTER_STATUSES)}"
        )


def test_front_matter_last_reviewed_is_iso_date() -> None:
    """Verify that last_reviewed contains a parseable ISO-8601 date, not a placeholder.

    Template files (``_template.md``) are excluded because they deliberately
    carry placeholder text such as ``YYYY-MM-DD``.  All published docs must
    carry a real review date so staleness can be detected automatically.
    """
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for path in iter_markdown_files():
        if path.name.startswith("_"):
            continue
        front_matter, _ = split_front_matter(path.read_text(encoding="utf-8"))
        raw = str(front_matter.get("last_reviewed", ""))
        assert date_pattern.match(raw), (
            f"{path.relative_to(REPO_ROOT)}: last_reviewed must be YYYY-MM-DD, got {raw!r}"
        )
        # Confirm the date is actually valid (e.g., not 2026-13-45).
        try:
            datetime.date.fromisoformat(raw)
        except ValueError as exc:
            raise AssertionError(
                f"{path.relative_to(REPO_ROOT)}: last_reviewed {raw!r} is not a valid calendar date"
            ) from exc


def test_front_matter_owner_is_non_empty_string() -> None:
    """Ensure the owner field carries a real value rather than an empty string.

    The front-matter key presence is already checked by
    ``test_every_published_markdown_page_has_required_front_matter``, but
    YAML allows ``owner:`` with no value, which evaluates to ``None``.  This
    test closes that gap.  Template files are excluded.
    """
    for path in iter_markdown_files():
        if path.name.startswith("_"):
            continue
        front_matter, _ = split_front_matter(path.read_text(encoding="utf-8"))
        owner = front_matter.get("owner")
        assert owner and str(owner).strip(), (
            f"{path.relative_to(REPO_ROOT)}: 'owner' must be a non-empty string, got {owner!r}"
        )


def test_oscal_files_are_non_empty_and_parseable() -> None:
    """Guard against empty or structurally broken OSCAL YAML files.

    ``test_oscal_files_have_required_metadata_and_valid_relative_hrefs`` calls
    ``next(iter(data))`` without checking whether ``yaml.safe_load`` returned
    ``None``.  An empty OSCAL file would cause a ``TypeError`` rather than a
    descriptive assertion failure.  This test provides the missing guard and
    gives a clear error message.
    """
    oscal_root = DOCS_ROOT / "compliance-mappings" / "oscal"
    yaml_files = list(oscal_root.rglob("*.yaml"))
    assert yaml_files, f"No OSCAL YAML files found under {oscal_root.relative_to(REPO_ROOT)}"
    for path in sorted(yaml_files):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict) and data, (
            f"{path.relative_to(REPO_ROOT)}: OSCAL file is empty or not a YAML mapping"
        )
