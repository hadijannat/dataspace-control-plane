"""DSP 2025-1 request and response message models.

All models represent DSP JSON-LD message shapes exactly as specified in
Dataspace Protocol 2025-1. They are used for both outbound (request) and
inbound (response/callback) messages.

Design rules:
- ``frozen=True`` — messages are value objects; once parsed they are never mutated.
- ``extra="forbid"`` — unknown DSP fields raise validation errors during TCK runs
  so we notice protocol drift early.
- ``populate_by_name=True`` — allows field access by Python name AND by alias.
- JSON-LD ``@context``, ``@type``, ``@id`` are aliased to valid Python identifiers.

JSON-LD context reference:
    https://w3id.org/dspace/2025/1/context.jsonld
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_DSP_CONTEXT = "https://w3id.org/dspace/2025/1/context.jsonld"
_DSP_VOCAB = "https://w3id.org/dspace/2025/1/vocab/"

_DEFAULT_CONTEXT: dict[str, str] = {"@vocab": _DSP_VOCAB}


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


class DspCatalogRequest(BaseModel):
    """DSP CatalogRequestMessage — sent by consumer to provider's catalog endpoint.

    DSP spec ref: §4.1 Catalog Protocol — CatalogRequestMessage
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    context: dict[str, Any] = Field(
        default_factory=lambda: _DEFAULT_CONTEXT,
        alias="@context",
    )
    type: str = Field("dspace:CatalogRequestMessage", alias="@type")
    filter: dict[str, Any] | None = Field(
        None,
        description="Optional ODRL filter expression to restrict catalog results",
    )


class DspCatalogResponse(BaseModel):
    """DSP Catalog response — returned by the provider's catalog endpoint.

    DSP spec ref: §4.2 Catalog Protocol — Catalog
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    context: dict[str, Any] = Field(alias="@context")
    type: str = Field("dcat:Catalog", alias="@type")
    datasets: list[dict[str, Any]] = Field(
        default_factory=list,
        alias="dcat:dataset",
        description="List of dcat:Dataset entries, each containing odrl:hasPolicy",
    )
    service: list[dict[str, Any]] | dict[str, Any] | None = Field(
        None,
        alias="dcat:service",
        description="Optional dcat:DataService entries",
    )


# ---------------------------------------------------------------------------
# Contract negotiation
# ---------------------------------------------------------------------------


class DspContractRequestMessage(BaseModel):
    """DSP ContractRequestMessage — sent by consumer to initiate negotiation.

    DSP spec ref: §5.3.1 Contract Negotiation Protocol — ContractRequestMessage
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    context: dict[str, Any] = Field(
        default_factory=lambda: _DEFAULT_CONTEXT,
        alias="@context",
    )
    type: str = Field("dspace:ContractRequestMessage", alias="@type")
    offer: dict[str, Any] = Field(
        ...,
        description="ODRL Offer dict (must include @id, @type='odrl:Offer', target)",
    )
    callback_address: str = Field(
        ...,
        alias="dspace:callbackAddress",
        description="Consumer's DSP callback URL for provider to POST events back",
    )
    dataset: str | None = Field(
        None,
        alias="dspace:dataset",
        description="Optional reference to the target dcat:Dataset",
    )


class DspContractOfferMessage(BaseModel):
    """DSP ContractOfferMessage — sent by provider during negotiation.

    DSP spec ref: §5.3.2 Contract Negotiation Protocol — ContractOfferMessage
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    context: dict[str, Any] = Field(
        default_factory=lambda: _DEFAULT_CONTEXT,
        alias="@context",
    )
    type: str = Field("dspace:ContractOfferMessage", alias="@type")
    offer: dict[str, Any] = Field(
        ...,
        description="ODRL Offer dict",
    )
    callback_address: str | None = Field(
        None,
        alias="dspace:callbackAddress",
        description="Provider's DSP callback URL",
    )


class DspContractAgreementMessage(BaseModel):
    """DSP ContractAgreementMessage — sent by provider when negotiation concludes.

    DSP spec ref: §5.3.4 Contract Negotiation Protocol — ContractAgreementMessage
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    context: dict[str, Any] = Field(
        default_factory=lambda: _DEFAULT_CONTEXT,
        alias="@context",
    )
    type: str = Field("dspace:ContractAgreementMessage", alias="@type")
    agreement: dict[str, Any] = Field(
        ...,
        description=(
            "ODRL Agreement dict — must include @id, @type='odrl:Agreement', "
            "target (asset IRI), timestamp, and consumer/provider DIDs"
        ),
    )
    callback_address: str | None = Field(
        None,
        alias="dspace:callbackAddress",
    )


class DspNegotiationEventMessage(BaseModel):
    """DSP ContractNegotiationEventMessage — asynchronous state-change notification.

    DSP spec ref: §5.3.5 Contract Negotiation Protocol — ContractNegotiationEventMessage

    The ``event_type`` field signals the transition:
    - ``"dspace:FINALIZED"``  — negotiation successfully concluded
    - ``"dspace:TERMINATED"`` — negotiation was terminated
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    context: dict[str, Any] = Field(
        default_factory=lambda: _DEFAULT_CONTEXT,
        alias="@context",
    )
    type: str = Field("dspace:ContractNegotiationEventMessage", alias="@type")
    provider_pid: str = Field(alias="dspace:providerPid")
    consumer_pid: str = Field(alias="dspace:consumerPid")
    event_type: str = Field(
        alias="dspace:eventType",
        description="Either 'dspace:FINALIZED' or 'dspace:TERMINATED'",
    )


# ---------------------------------------------------------------------------
# Transfer
# ---------------------------------------------------------------------------


class DspTransferRequestMessage(BaseModel):
    """DSP TransferRequestMessage — sent by consumer to initiate data transfer.

    DSP spec ref: §6.3.1 Transfer Process Protocol — TransferRequestMessage
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    context: dict[str, Any] = Field(
        default_factory=lambda: _DEFAULT_CONTEXT,
        alias="@context",
    )
    type: str = Field("dspace:TransferRequestMessage", alias="@type")
    agreement_id: str = Field(
        alias="dspace:agreementId",
        description="@id of the concluded ContractAgreement",
    )
    format: str = Field(
        alias="dspace:format",
        description="Transfer format IRI (e.g. 'dspace:HTTP_PULL')",
    )
    callback_address: str = Field(
        alias="dspace:callbackAddress",
        description="Consumer's DSP callback URL for transfer events",
    )
    data_address: dict[str, Any] | None = Field(
        None,
        alias="dspace:dataAddress",
        description="Optional explicit data destination address",
    )


class DspTransferStartMessage(BaseModel):
    """DSP TransferStartMessage — sent by provider when transfer data flow begins.

    DSP spec ref: §6.3.2 Transfer Process Protocol — TransferStartMessage
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    context: dict[str, Any] = Field(
        default_factory=lambda: _DEFAULT_CONTEXT,
        alias="@context",
    )
    type: str = Field("dspace:TransferStartMessage", alias="@type")
    provider_pid: str = Field(alias="dspace:providerPid")
    consumer_pid: str = Field(alias="dspace:consumerPid")
    data_address: dict[str, Any] | None = Field(
        None,
        alias="dspace:dataAddress",
        description="Endpoint information for consumer-pull transfers",
    )
