"""Battery passport integration with ESPR registry mechanics.

The ESPR registry stores battery identifiers referenced by the Battery Regulation.
This module defines how battery pack data maps to registry payloads WITHOUT
subclassing or importing from espr_dpp — the battery law and ESPR are
separate legal instruments with distinct lifecycle and access models.

Reference:
  Regulation (EU) 2023/1542, Art. 74 — ESPR registry reference.
  Regulation (EU) 2024/1781 (ESPR) — registry operator.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BatteryRegistryPayload:
    """Canonical payload for registering a battery passport in the ESPR registry."""

    battery_id: str
    dpp_id: str
    battery_type: str
    """e.g. 'lmt', 'industrial', 'ev'"""
    lifecycle_state: str
    registry_url: str | None = None
    """URI of the ESPR registry endpoint. None until registry is operational (target: 2026-07-19)."""
    espr_registry_ref: str | None = None
    """Reference to the ESPR registry entry, if the battery identifier has been registered there."""

    def as_dict(self) -> dict[str, Any]:
        return {
            "battery_id": self.battery_id,
            "dpp_id": self.dpp_id,
            "battery_type": self.battery_type,
            "lifecycle_state": self.lifecycle_state,
            "registry_url": self.registry_url,
            "espr_registry_ref": self.espr_registry_ref,
        }


def build_battery_registry_payload(
    battery_id: str,
    dpp_id: str,
    battery_type: str,
    lifecycle_state: str,
    *,
    registry_url: str | None = None,
    espr_registry_ref: str | None = None,
) -> dict[str, Any]:
    """Build a canonical battery registry payload dict.

    Note: The ESPR Commission registry is expected to be operational by 2026-07-19.
    Until then, ``registry_url`` may be None and the payload can be stored locally
    as evidence for future registration.
    """
    return BatteryRegistryPayload(
        battery_id=battery_id,
        dpp_id=dpp_id,
        battery_type=battery_type,
        lifecycle_state=lifecycle_state,
        registry_url=registry_url,
        espr_registry_ref=espr_registry_ref,
    ).as_dict()
