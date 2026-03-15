"""MX-Port Adapter layer profiles.

The Adapter layer provides attachment points for business applications such
as shop-floor systems and ERP integrations.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AdapterProfile:
    """An Adapter layer profile for a business-application attachment.

    Attributes:
        adapter_id:          Unique identifier for this adapter.
        attachment_protocol: Protocol used to attach to the adapter
                             (e.g. ``"aas-rest"``, ``"opc-ua"``, ``"http"``).
        capabilities:        Sorted tuple of capability strings this adapter provides.
    """

    adapter_id: str
    attachment_protocol: str
    capabilities: tuple[str, ...]

    def __init__(
        self,
        adapter_id: str,
        attachment_protocol: str,
        capabilities: list[str],
    ) -> None:
        object.__setattr__(self, "adapter_id", adapter_id)
        object.__setattr__(self, "attachment_protocol", attachment_protocol)
        object.__setattr__(self, "capabilities", tuple(sorted(capabilities)))


# ---------------------------------------------------------------------------
# Standard adapter profiles
# ---------------------------------------------------------------------------

SHOP_FLOOR_ADAPTER = AdapterProfile(
    adapter_id="adapter:shop-floor",
    attachment_protocol="opc-ua",
    capabilities=["machine-data-read", "process-parameter-read", "alarm-read"],
)
"""Shop-floor / MES adapter using OPC UA as the attachment protocol."""

ERP_ADAPTER = AdapterProfile(
    adapter_id="adapter:erp",
    attachment_protocol="http",
    capabilities=["order-read", "inventory-read", "production-order-read"],
)
"""ERP adapter using HTTP as the attachment protocol."""
