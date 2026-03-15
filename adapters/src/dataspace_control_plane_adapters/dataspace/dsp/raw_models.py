"""DSP wire-format raw models.

Re-exports all DSP message classes from ``messages.py`` under the ``raw_models``
name so that the adapter's internal structure is consistent with other adapter
packages that define inbound wire shapes in ``raw_models.py``.

DSP is symmetric: the same Pydantic models describe both inbound and outbound
messages, so a separate inbound-only model file is not needed.
"""
from __future__ import annotations

from .messages import (
    DspCatalogRequest,
    DspCatalogResponse,
    DspContractAgreementMessage,
    DspContractOfferMessage,
    DspContractRequestMessage,
    DspNegotiationEventMessage,
    DspTransferRequestMessage,
    DspTransferStartMessage,
)

__all__ = [
    "DspCatalogRequest",
    "DspCatalogResponse",
    "DspContractRequestMessage",
    "DspContractOfferMessage",
    "DspContractAgreementMessage",
    "DspNegotiationEventMessage",
    "DspTransferRequestMessage",
    "DspTransferStartMessage",
]
