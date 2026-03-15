from __future__ import annotations

import dataclasses
import importlib
import inspect
import pkgutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog
from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ProcedureDefinition:
    slug: str
    module_name: str
    workflow_type: str
    task_queue: str
    workflow_id_template: str
    search_attribute_keys: tuple[str, ...]
    conflict_policy: str
    input_type: type[Any]


class ProcedureCatalog:
    def __init__(self, definitions: dict[str, ProcedureDefinition]) -> None:
        self._definitions = definitions

    @classmethod
    def discover(cls) -> "ProcedureCatalog":
        try:
            procedures_pkg = cls._import_procedures_package()
        except ImportError as exc:
            logger.warning("procedure_catalog.unavailable", error=str(exc))
            return cls({})

        definitions: dict[str, ProcedureDefinition] = {}
        for module_info in pkgutil.iter_modules(procedures_pkg.__path__):
            module_name = module_info.name
            if module_name.startswith("_") or not module_info.ispkg:
                continue

            api_module = importlib.import_module(
                f"{procedures_pkg.__name__}.{module_name}.api"
            )
            manifest = getattr(api_module, "MANIFEST", None)
            if manifest is None:
                logger.debug("procedure_catalog.skip_missing_manifest", module=module_name)
                continue

            input_type = cls._discover_input_type(procedures_pkg.__name__, module_name, api_module)
            if input_type is None:
                logger.warning(
                    "procedure_catalog.skip_missing_input_type",
                    module=module_name,
                )
                continue

            slug = module_name.replace("_", "-")
            definitions[slug] = ProcedureDefinition(
                slug=slug,
                module_name=module_name,
                workflow_type=manifest.workflow_type,
                task_queue=manifest.task_queue,
                workflow_id_template=manifest.workflow_id_template,
                search_attribute_keys=tuple(manifest.search_attribute_keys),
                conflict_policy=manifest.conflict_policy,
                input_type=input_type,
            )

        logger.info(
            "procedure_catalog.loaded",
            procedures=sorted(definitions),
            count=len(definitions),
        )
        return cls(definitions)

    @staticmethod
    def _import_procedures_package():
        try:
            import dataspace_control_plane_procedures as procedures_pkg
            return procedures_pkg
        except ImportError:
            repo_procedures_src = Path(__file__).resolve().parents[4] / "procedures" / "src"
            if repo_procedures_src.exists():
                sys.path.insert(0, str(repo_procedures_src))
            import dataspace_control_plane_procedures as procedures_pkg
            return procedures_pkg

    @staticmethod
    def _discover_input_type(
        package_name: str,
        module_name: str,
        api_module: Any,
    ) -> type[Any] | None:
        input_types: list[type[Any]] = []
        for candidate_module in (
            api_module,
            importlib.import_module(f"{package_name}.{module_name}.input"),
        ):
            input_types.extend(
                value
                for _, value in vars(candidate_module).items()
                if inspect.isclass(value)
                and dataclasses.is_dataclass(value)
                and value.__name__.endswith("StartInput")
            )
            if input_types:
                break
        if len(input_types) != 1:
            return None
        return input_types[0]

    def resolve(self, procedure_type: str) -> ProcedureDefinition:
        definition = self._definitions.get(procedure_type)
        if definition is None:
            raise ValueError(
                f"Unknown procedure type '{procedure_type}'. "
                f"Known types: {sorted(self._definitions)}"
            )
        return definition

    def available_types(self) -> list[str]:
        return sorted(self._definitions)

    def build_workflow_input(
        self,
        definition: ProcedureDefinition,
        *,
        tenant_id: str,
        legal_entity_id: str | None,
        payload: dict[str, Any],
        idempotency_key: str | None,
    ) -> Any:
        field_names = {field.name for field in dataclasses.fields(definition.input_type)}
        merged: dict[str, Any] = dict(payload)
        merged.setdefault("tenant_id", tenant_id)
        if legal_entity_id is not None:
            merged.setdefault("legal_entity_id", legal_entity_id)
        if idempotency_key is not None and "idempotency_key" in field_names:
            merged.setdefault("idempotency_key", idempotency_key)

        kwargs = {key: value for key, value in merged.items() if key in field_names}
        try:
            return definition.input_type(**kwargs)
        except TypeError as exc:
            raise ValueError(
                f"Invalid payload for procedure '{definition.slug}': {exc}"
            ) from exc

    def build_workflow_id(
        self,
        definition: ProcedureDefinition,
        workflow_input: Any,
    ) -> str:
        values = {
            field.name: getattr(workflow_input, field.name)
            for field in dataclasses.fields(workflow_input)
        }
        try:
            return definition.workflow_id_template.format_map(values)
        except KeyError as exc:
            missing = exc.args[0]
            raise ValueError(
                f"Missing workflow id field '{missing}' for procedure '{definition.slug}'"
            ) from exc

    def build_search_attributes(
        self,
        definition: ProcedureDefinition,
        workflow_input: Any,
    ) -> dict[str, list[str]]:
        values = {
            field.name: getattr(workflow_input, field.name)
            for field in dataclasses.fields(workflow_input)
        }
        attrs: dict[str, list[str]] = {}
        for key in definition.search_attribute_keys:
            if key == "procedure_type":
                attrs[key] = [definition.slug]
            elif key == "status":
                attrs[key] = ["STARTED"]
            else:
                value = values.get(key)
                if value not in (None, ""):
                    attrs[key] = [str(value)]
        return attrs

    def build_conflict_policy(
        self,
        definition: ProcedureDefinition,
    ) -> tuple[WorkflowIDConflictPolicy, WorkflowIDReusePolicy]:
        if definition.conflict_policy == "use_existing":
            return (
                WorkflowIDConflictPolicy.USE_EXISTING,
                WorkflowIDReusePolicy.ALLOW_DUPLICATE,
            )
        if definition.conflict_policy == "reject":
            return (
                WorkflowIDConflictPolicy.FAIL,
                WorkflowIDReusePolicy.REJECT_DUPLICATE,
            )
        return (
            WorkflowIDConflictPolicy.UNSPECIFIED,
            WorkflowIDReusePolicy.ALLOW_DUPLICATE,
        )
