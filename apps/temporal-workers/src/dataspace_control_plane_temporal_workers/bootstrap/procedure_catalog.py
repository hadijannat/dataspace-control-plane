from __future__ import annotations

from dataclasses import dataclass

from dataspace_control_plane_procedures import discover_definitions


@dataclass(frozen=True)
class ProcedureManifestInfo:
    module_name: str
    workflow_type: str
    task_queue: str
    search_attribute_keys: tuple[str, ...]


def import_procedures_package():
    import dataspace_control_plane_procedures as procedures_pkg

    return procedures_pkg


def load_procedure_manifests() -> dict[str, ProcedureManifestInfo]:
    return {
        definition.name: ProcedureManifestInfo(
            module_name=definition.module_name,
            workflow_type=definition.workflow_type,
            task_queue=definition.task_queue,
            search_attribute_keys=tuple(definition.manifest.search_attribute_keys),
        )
        for definition in discover_definitions()
    }
