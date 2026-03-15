"""DSP inbound message validators.

Every DSP message arriving from an external connector must be validated here
before it crosses the adapter boundary into core/. Validation uses the shared
``parse_model`` helper which translates Pydantic ``ValidationError`` into
``AdapterValidationError``.

Rules:
- Raise ``DspValidationError`` (not raw Pydantic errors) on invalid input.
- Never mutate the input dict.
- Pure functions; no I/O.
"""
from __future__ import annotations

from ..._shared.serde import parse_model
from ..._shared.errors import AdapterValidationError
from .errors import DspValidationError
from .messages import (
    DspCatalogRequest,
    DspContractAgreementMessage,
    DspContractOfferMessage,
    DspContractRequestMessage,
    DspNegotiationEventMessage,
    DspTransferRequestMessage,
)


def _wrap(func):  # type: ignore[no-untyped-def]
    """Decorator that re-raises AdapterValidationError as DspValidationError."""

    def wrapper(raw: dict) -> object:  # type: ignore[type-arg]
        try:
            return func(raw)
        except AdapterValidationError as exc:
            raise DspValidationError(str(exc)) from exc

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


@_wrap
def validate_catalog_request(raw: dict) -> DspCatalogRequest:  # type: ignore[return]
    """Validate and parse a DSP CatalogRequestMessage.

    Args:
        raw: Raw dict parsed from the incoming HTTP request body.

    Returns:
        Validated ``DspCatalogRequest`` instance.

    Raises:
        DspValidationError: If the message does not conform to the DSP schema.
    """
    return parse_model(DspCatalogRequest, raw)


@_wrap
def validate_contract_request(raw: dict) -> DspContractRequestMessage:  # type: ignore[return]
    """Validate and parse a DSP ContractRequestMessage.

    Args:
        raw: Raw dict from the incoming negotiation request body.

    Returns:
        Validated ``DspContractRequestMessage`` instance.

    Raises:
        DspValidationError: If the message does not conform to the DSP schema.
    """
    return parse_model(DspContractRequestMessage, raw)


@_wrap
def validate_contract_offer(raw: dict) -> DspContractOfferMessage:  # type: ignore[return]
    """Validate and parse a DSP ContractOfferMessage.

    Args:
        raw: Raw dict from the provider's offer response body.

    Returns:
        Validated ``DspContractOfferMessage`` instance.

    Raises:
        DspValidationError: If the message does not conform to the DSP schema.
    """
    return parse_model(DspContractOfferMessage, raw)


@_wrap
def validate_agreement_message(raw: dict) -> DspContractAgreementMessage:  # type: ignore[return]
    """Validate and parse a DSP ContractAgreementMessage.

    Args:
        raw: Raw dict from the provider's agreement notification body.

    Returns:
        Validated ``DspContractAgreementMessage`` instance.

    Raises:
        DspValidationError: If the message does not conform to the DSP schema.
    """
    return parse_model(DspContractAgreementMessage, raw)


@_wrap
def validate_negotiation_event(raw: dict) -> DspNegotiationEventMessage:  # type: ignore[return]
    """Validate and parse a DSP ContractNegotiationEventMessage.

    Args:
        raw: Raw dict from the provider's event callback body.

    Returns:
        Validated ``DspNegotiationEventMessage`` instance.

    Raises:
        DspValidationError: If the message does not conform to the DSP schema.
    """
    return parse_model(DspNegotiationEventMessage, raw)


@_wrap
def validate_transfer_request(raw: dict) -> DspTransferRequestMessage:  # type: ignore[return]
    """Validate and parse a DSP TransferRequestMessage.

    Args:
        raw: Raw dict from the consumer's transfer initiation body.

    Returns:
        Validated ``DspTransferRequestMessage`` instance.

    Raises:
        DspValidationError: If the message does not conform to the DSP schema.
    """
    return parse_model(DspTransferRequestMessage, raw)
