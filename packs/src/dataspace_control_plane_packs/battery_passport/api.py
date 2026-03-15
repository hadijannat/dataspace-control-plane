"""Public import surface for the EU Battery Regulation pack."""
from __future__ import annotations

import pathlib
from typing import Any

from .._shared.capabilities import PackCapability
from .._shared.interfaces import TwinTemplateProvider
from .._shared.manifest import PackManifest
from .._shared.rule_model import ValidationResult
from .annex_xiii.access_matrix import build_battery_access_matrix
from .annex_xiii.public_fields import PUBLIC_FIELDS
from .annex_xiii.authority_fields import AUTHORITY_FIELDS
from .annex_xiii.legitimate_interest_fields import LEGITIMATE_INTEREST_FIELDS
from .evidence import BatteryEvidenceAugmenter
from .identifiers import BatteryIdentifierValidator, BATTERY_ID_REQUIRED, QR_ACCESS_REQUIRED
from .implementation_profiles.aas_dpp4o.battery_submodels import build_battery_passport_submodel
from .lifecycle import BatteryLifecycleProvider, BatteryState
from .linkage import PassportLink, build_passport_link, validate_linkage
from .registry_bridge import BatteryRegistryPayload, build_battery_registry_payload
from .requirements import BatteryRequirementProvider

_MANIFEST_PATH = pathlib.Path(__file__).parent / "manifest.toml"
MANIFEST: PackManifest = PackManifest.from_toml(_MANIFEST_PATH)


class BatteryAasTwinTemplateProvider:
    """TwinTemplateProvider for battery passport AAS submodels."""

    def templates(self, *, context: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "template_id": "battery_passport_v1",
                "submodel": "BatteryPassport",
                "semantic_id": "https://admin-shell.io/idta/battery-passport/1/0",
                "description": "EU Battery Regulation Annex XIII battery passport submodel",
            }
        ]

    def apply_template(
        self,
        template_id: str,
        subject: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        battery_id = subject.get("battery_id", "unknown")
        return build_battery_passport_submodel(battery_id, subject)


PROVIDERS: dict[PackCapability, Any] = {
    PackCapability.REQUIREMENT_PROVIDER: BatteryRequirementProvider(),
    PackCapability.LIFECYCLE_MODEL: BatteryLifecycleProvider(),
    PackCapability.EVIDENCE_AUGMENTER: BatteryEvidenceAugmenter(),
    PackCapability.TWIN_TEMPLATE: BatteryAasTwinTemplateProvider(),
}

__all__ = [
    "MANIFEST",
    "PROVIDERS",
    "BatteryRequirementProvider",
    "BatteryLifecycleProvider",
    "BatteryEvidenceAugmenter",
    "BatteryIdentifierValidator",
    "PassportLink",
    "BatteryRegistryPayload",
    "BatteryState",
    "build_battery_access_matrix",
    "BatteryAasTwinTemplateProvider",
    "build_battery_passport_submodel",
    "build_passport_link",
    "build_battery_registry_payload",
    "validate_linkage",
    "PUBLIC_FIELDS",
    "AUTHORITY_FIELDS",
    "LEGITIMATE_INTEREST_FIELDS",
    "BATTERY_ID_REQUIRED",
    "QR_ACCESS_REQUIRED",
]
