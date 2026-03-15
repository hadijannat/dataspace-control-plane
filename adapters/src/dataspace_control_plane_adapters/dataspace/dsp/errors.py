"""DSP adapter error hierarchy.

These errors are raised by DSP adapter internals and must be translated at the
ports_impl.py boundary before propagating into procedures/ or apps/.
"""
from __future__ import annotations

from ..._shared.errors import (
    AdapterError,
    AdapterValidationError,
)


class DspError(AdapterError):
    """Root for all DSP adapter errors."""


class DspValidationError(AdapterValidationError):
    """A DSP inbound message failed JSON-LD schema or semantic validation."""


class DspNegotiationError(DspError):
    """Error during DSP contract negotiation message processing."""


class DspTransferError(DspError):
    """Error during DSP transfer message processing."""
