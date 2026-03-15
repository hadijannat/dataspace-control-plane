from __future__ import annotations

import importlib
import pkgutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcedureManifestInfo:
    module_name: str
    workflow_type: str
    task_queue: str
    search_attribute_keys: tuple[str, ...]


def import_procedures_package():
    try:
        import dataspace_control_plane_procedures as procedures_pkg
        return procedures_pkg
    except ImportError:
        repo_procedures_src = Path(__file__).resolve().parents[4] / "procedures" / "src"
        if repo_procedures_src.exists():
            sys.path.insert(0, str(repo_procedures_src))
        import dataspace_control_plane_procedures as procedures_pkg
        return procedures_pkg


def load_procedure_manifests() -> dict[str, ProcedureManifestInfo]:
    procedures_pkg = import_procedures_package()
    manifests: dict[str, ProcedureManifestInfo] = {}
    for module_info in pkgutil.iter_modules(procedures_pkg.__path__):
        if module_info.name.startswith("_") or not module_info.ispkg:
            continue
        manifest_module = importlib.import_module(
            f"{procedures_pkg.__name__}.{module_info.name}.manifest"
        )
        manifest = getattr(manifest_module, "MANIFEST", None)
        if manifest is None:
            continue
        slug = module_info.name.replace("_", "-")
        manifests[slug] = ProcedureManifestInfo(
            module_name=module_info.name,
            workflow_type=manifest.workflow_type,
            task_queue=manifest.task_queue,
            search_attribute_keys=tuple(manifest.search_attribute_keys),
        )
    return manifests
