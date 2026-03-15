from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class ProcedureManifest:
    """Static metadata describing a procedure family."""
    workflow_type: str
    task_queue: str
    workflow_id_template: str          # e.g. "company-onboarding:{tenant_id}:{lei}"
    search_attribute_keys: tuple[str, ...] = field(default_factory=tuple)
    supported_packs: tuple[str, ...] = field(default_factory=tuple)
    version_markers: tuple[str, ...] = field(default_factory=tuple)
    lifecycle: Literal["one_shot", "entity", "scheduled"] = "one_shot"
    conflict_policy: Literal["reject", "use_existing", "allow"] = "reject"
    supports_manual_review: bool = False
    supports_continue_as_new: bool = False
