#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import copy
import yaml


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "base"
PROFILE_DIR = ROOT / "profiles"
ENV_DIR = ROOT / "env"
HELM_SOURCE_DIR = ROOT / "helm" / "source"
HELM_OUTPUT_DIR = ROOT / "helm"
DOCKER_OUTPUT_DIR = ROOT / "docker"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def deep_merge(base: dict, overlay: dict) -> dict:
    merged = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and not value:
            merged[key] = {}
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def build_collector_config(profile: str, env: str) -> dict:
    config = {}
    for filename in (
        "receivers.yaml",
        "processors.yaml",
        "exporters.yaml",
        "extensions.yaml",
        "collector.yaml",
    ):
        config = deep_merge(config, load_yaml(BASE_DIR / filename))
    config = deep_merge(config, load_yaml(PROFILE_DIR / f"{profile}.yaml"))
    config = deep_merge(config, load_yaml(ENV_DIR / f"{env}.yaml"))
    return config


def write_yaml(path: Path, data: dict, header: str) -> None:
    rendered = yaml.safe_dump(data, sort_keys=False)
    path.write_text(f"{header}\n{rendered}", encoding="utf-8")


def render_docker_dev() -> None:
    config = build_collector_config("debug", "dev")
    write_yaml(
        DOCKER_OUTPUT_DIR / "collector.dev.yaml",
        config,
        "# Generated from base + debug profile + dev env. Do not edit directly.",
    )


def render_helm_values(env: str) -> None:
    wrapper = load_yaml(HELM_SOURCE_DIR / f"{env}.yaml")
    wrapper["config"] = build_collector_config("gateway", env)
    write_yaml(
        HELM_OUTPUT_DIR / f"values.{env}.yaml",
        wrapper,
        f"# Generated from helm/source/{env}.yaml + base + gateway profile + {env} env. Do not edit directly.",
    )


def main() -> None:
    render_docker_dev()
    for env in ("dev", "staging", "prod-eu"):
        render_helm_values(env)


if __name__ == "__main__":
    main()
