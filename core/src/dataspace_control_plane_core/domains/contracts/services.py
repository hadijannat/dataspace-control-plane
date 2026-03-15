from __future__ import annotations
from datetime import datetime, timezone

from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId
from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .commands import (
    StartNegotiationCommand, SubmitOfferCommand,
    ConcludeAgreementCommand, TerminateNegotiationCommand,
    RevokeEntitlementCommand,
)
from .model.aggregates import NegotiationCase, Entitlement
from .model.value_objects import OfferSnapshot, AgreementRecord
from .ports import NegotiationRepository, EntitlementRepository


class ContractService:
    def __init__(
        self,
        negotiations: NegotiationRepository,
        entitlements: EntitlementRepository,
        clock: Clock = UtcClock(),
    ) -> None:
        self._negotiations = negotiations
        self._entitlements = entitlements
        self._clock = clock

    async def start_negotiation(self, cmd: StartNegotiationCommand) -> NegotiationCase:
        negotiation = NegotiationCase(
            id=AggregateId.generate(),
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            counterparty=cmd.counterparty,
            asset=cmd.asset,
            started_at=self._clock.now(),
        )
        offer = OfferSnapshot(
            offer_id=cmd.initial_offer_id,
            policy_id=cmd.policy_id,
            asset=cmd.asset,
            provider=cmd.counterparty,
        )
        negotiation.submit_offer(offer)
        await self._negotiations.save(cmd.tenant_id, negotiation)
        return negotiation

    async def submit_offer(self, cmd: SubmitOfferCommand) -> NegotiationCase:
        negotiation = await self._negotiations.get(cmd.tenant_id, cmd.negotiation_id)
        offer = OfferSnapshot(
            offer_id=cmd.offer_id,
            policy_id=cmd.policy_id,
            asset=negotiation.asset,
            provider=negotiation.counterparty,
            valid_until=cmd.valid_until,
        )
        negotiation.submit_offer(offer)
        await self._negotiations.save(cmd.tenant_id, negotiation)
        return negotiation

    async def conclude_agreement(self, cmd: ConcludeAgreementCommand) -> tuple[NegotiationCase, Entitlement]:
        negotiation = await self._negotiations.get(cmd.tenant_id, cmd.negotiation_id)
        agreement = AgreementRecord(
            agreement_id=cmd.agreement_id,
            policy_snapshot_id=cmd.policy_snapshot_id,
            asset=negotiation.asset,
            provider=negotiation.counterparty,
            consumer=negotiation.counterparty,  # adapter resolves actual consumer
            concluded_at=cmd.concluded_at,
        )
        negotiation.conclude_agreement(agreement)
        await self._negotiations.save(cmd.tenant_id, negotiation)

        entitlement = Entitlement(
            id=AggregateId.generate(),
            tenant_id=cmd.tenant_id,
            legal_entity_id=negotiation.legal_entity_id,
            agreement_id=cmd.agreement_id,
            asset_id=negotiation.asset.asset_id if negotiation.asset else "",
            purpose="",
            counterparty_id=negotiation.counterparty.connector_id if negotiation.counterparty else "",
            valid_from=self._clock.now(),
        )
        await self._entitlements.save(cmd.tenant_id, entitlement)
        return negotiation, entitlement

    async def terminate_negotiation(self, cmd: TerminateNegotiationCommand) -> NegotiationCase:
        negotiation = await self._negotiations.get(cmd.tenant_id, cmd.negotiation_id)
        negotiation.terminate(cmd.reason)
        await self._negotiations.save(cmd.tenant_id, negotiation)
        return negotiation

    async def revoke_entitlement(self, cmd: RevokeEntitlementCommand) -> Entitlement:
        entitlement = await self._entitlements.get(cmd.tenant_id, cmd.entitlement_id)
        entitlement.revoke()
        await self._entitlements.save(cmd.tenant_id, entitlement)
        return entitlement
