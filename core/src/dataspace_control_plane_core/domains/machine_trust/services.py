from __future__ import annotations
from dataspace_control_plane_core.domains._shared.ids import AggregateId
from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .commands import RegisterDidCommand, AddCredentialCommand, RevokeCredentialCommand
from .events import DidRegistered, CredentialAdded, CredentialRevoked
from .model.aggregates import TrustParticipant
from .ports import TrustParticipantRepository


class MachineTrustService:
    def __init__(self, repo: TrustParticipantRepository, clock: Clock = UtcClock()) -> None:
        self._repo = repo
        self._clock = clock

    async def register_did(self, cmd: RegisterDidCommand) -> TrustParticipant:
        participant = TrustParticipant(
            id=AggregateId.generate(),
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            did=cmd.did,
        )
        participant._raise_event(DidRegistered(
            tenant_id=cmd.tenant_id, did_uri=str(cmd.did)
        ))
        await self._repo.save(participant, expected_version=0)
        return participant

    async def add_credential(self, cmd: AddCredentialCommand) -> TrustParticipant:
        participant = await self._repo.get(cmd.tenant_id, cmd.legal_entity_id)
        participant.add_credential(cmd.credential)
        participant._raise_event(CredentialAdded(
            tenant_id=cmd.tenant_id,
            credential_id=cmd.credential.id,
            credential_type=",".join(cmd.credential.type_labels),
        ))
        await self._repo.save(participant, expected_version=participant.version)
        return participant
