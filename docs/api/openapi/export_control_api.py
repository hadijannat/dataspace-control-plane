from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
CONTROL_API_ROOT = REPO_ROOT / "apps" / "control-api"
SOURCE_SPEC_PATH = Path(__file__).resolve().parent / "source" / "control-api.yaml"


def _bootstrap_import_path() -> None:
    control_api_path = str(CONTROL_API_ROOT)
    if control_api_path not in sys.path:
        sys.path.insert(0, control_api_path)


def _bootstrap_env() -> None:
    os.environ.setdefault("CONTROL_API_DEBUG", "true")
    os.environ.setdefault("CONTROL_API_DOCS_PUBLIC", "true")
    os.environ.setdefault(
        "CONTROL_API_STREAM_TICKET_SECRET",
        "docs-export-stream-ticket-secret-0123456789",
    )


def build_schema() -> dict:
    _bootstrap_env()
    _bootstrap_import_path()

    from app.main import app

    app.openapi_schema = None
    schema = app.openapi()
    info = schema.setdefault("info", {})
    schema.setdefault(
        "servers",
        [
            {
                "url": "/",
                "description": "Environment-relative deployment base URL.",
            }
        ],
    )
    license_info = info.setdefault("license", {})
    license_info.setdefault("name", "Proprietary - Internal Use Only")
    license_info.setdefault("identifier", "LicenseRef-Proprietary-Internal-Use-Only")
    return schema


def export_source_spec() -> dict:
    schema = build_schema()
    SOURCE_SPEC_PATH.write_text(
        yaml.safe_dump(schema, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return schema


if __name__ == "__main__":
    export_source_spec()
