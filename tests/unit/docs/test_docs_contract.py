from __future__ import annotations

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


def iter_markdown_files() -> list[Path]:
    return sorted(
        path
        for path in DOCS_ROOT.rglob("*.md")
        if not EXCLUDED_DOC_PATH_PARTS.intersection(path.parts)
    )


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
    return yaml.load(MKDOCS_CONFIG_PATH.read_text(encoding="utf-8"), Loader=yaml.Loader)


def load_openapi_export_module():
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
