"""Pydantic models for the EDC wire format.

EDC uses JSON-LD with ``@context``, ``@type``, and ``@id`` fields.
These raw models capture exactly what EDC returns on the wire — they are
never promoted to domain aggregates.

Rules:
- ``frozen=True``: wire models are value objects, never mutated.
- ``extra="forbid"``: unknown EDC fields raise validation errors so we notice
  protocol changes early during tests.
- Field aliases map JSON-LD keys (``@id``, ``@type``) to valid Python names.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EdcAssetRaw(BaseModel):
    """Wire shape for a single EDC asset as returned by GET /v2/assets/{id}."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    id: str = Field(alias="@id")
    type: str = Field("edc:Asset", alias="@type")
    properties: dict[str, Any] = Field(default_factory=dict, alias="edc:properties")
    data_address: dict[str, Any] | None = Field(
        None, alias="edc:dataAddress"
    )
    private_properties: dict[str, Any] = Field(
        default_factory=dict, alias="edc:privateProperties"
    )


class EdcPolicyDefinitionRaw(BaseModel):
    """Wire shape for a single EDC policy definition."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    id: str = Field(alias="@id")
    type: str = Field("edc:PolicyDefinition", alias="@type")
    policy: dict[str, Any] = Field(alias="edc:policy")
    created_at: int | None = Field(None, alias="edc:createdAt")


class EdcContractOfferRaw(BaseModel):
    """Wire shape for a contract offer embedded inside an EDC catalog dataset."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    id: str = Field(alias="@id")
    type: str = Field("odrl:Offer", alias="@type")
    policy: dict[str, Any] = Field(default_factory=dict)
    asset_id: str | None = Field(None, alias="edc:assetId")


class EdcDatasetRaw(BaseModel):
    """Wire shape for a dataset entry inside an EDC catalog."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    id: str = Field(alias="@id")
    type: str | None = Field(None, alias="@type")
    has_policy: list[EdcContractOfferRaw] | EdcContractOfferRaw | None = Field(
        None, alias="odrl:hasPolicy"
    )
    properties: dict[str, Any] = Field(default_factory=dict)


class EdcCatalogRaw(BaseModel):
    """Wire shape for the EDC catalog response (POST /v2/catalog/request)."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    id: str = Field(alias="@id")
    type: str = Field("dcat:Catalog", alias="@type")
    datasets: list[EdcDatasetRaw] = Field(
        default_factory=list, alias="dcat:dataset"
    )
    service: list[dict[str, Any]] | dict[str, Any] | None = Field(
        None, alias="dcat:service"
    )


class EdcNegotiationRaw(BaseModel):
    """Wire shape for an EDC contract negotiation as returned by the management API."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    id: str = Field(alias="@id")
    type: str = Field("edc:ContractNegotiation", alias="@type")
    state: str = Field(alias="edc:state")
    contract_agreement_id: str | None = Field(None, alias="edc:contractAgreementId")
    counter_party_address: str | None = Field(None, alias="edc:counterPartyAddress")
    error_detail: str | None = Field(None, alias="edc:errorDetail")
    created_at: int | None = Field(None, alias="edc:createdAt")


class EdcContractAgreementRaw(BaseModel):
    """Wire shape for an EDC contract agreement."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    id: str = Field(alias="@id")
    type: str = Field("edc:ContractAgreement", alias="@type")
    asset_id: str = Field(alias="edc:assetId")
    policy: dict[str, Any] = Field(alias="edc:policy")
    consumer_id: str | None = Field(None, alias="edc:consumerId")
    provider_id: str | None = Field(None, alias="edc:providerId")
    contract_signing_date: int | None = Field(None, alias="edc:contractSigningDate")


class EdcTransferProcessRaw(BaseModel):
    """Wire shape for an EDC transfer process."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    id: str = Field(alias="@id")
    type: str = Field("edc:TransferProcess", alias="@type")
    state: str = Field(alias="edc:state")
    asset_id: str | None = Field(None, alias="edc:assetId")
    contract_agreement_id: str | None = Field(None, alias="edc:contractAgreementId")
    data_destination: dict[str, Any] | None = Field(None, alias="edc:dataDestination")
    error_detail: str | None = Field(None, alias="edc:errorDetail")
    created_at: int | None = Field(None, alias="edc:createdAt")
