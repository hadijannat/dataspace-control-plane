from __future__ import annotations
from dataspace_control_plane_core.domains._shared.ids import AggregateId
from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .commands import CreatePolicyTemplateCommand, ActivatePolicyTemplateCommand
from .events import PolicyTemplateCreated, PolicyTemplateActivated
from .model.aggregates import PolicyTemplate
from .ports import PolicyTemplateRepository


class PolicyService:
    def __init__(self, repo: PolicyTemplateRepository, clock: Clock = UtcClock()) -> None:
        self._repo = repo
        self._clock = clock

    async def create_template(self, cmd: CreatePolicyTemplateCommand) -> PolicyTemplate:
        template = PolicyTemplate(
            id=AggregateId.generate(),
            tenant_id=cmd.tenant_id,
            name=cmd.name,
            description=cmd.description,
            canonical_policy=cmd.canonical_policy,
        )
        template._raise_event(PolicyTemplateCreated(
            tenant_id=cmd.tenant_id,
            policy_id=str(template.id),
            name=cmd.name,
            has_parse_losses=template.has_parse_losses(),
        ))
        await self._repo.save(template, expected_version=0)
        return template

    async def activate_template(self, cmd: ActivatePolicyTemplateCommand) -> PolicyTemplate:
        template = await self._repo.get(cmd.tenant_id, cmd.policy_id)
        template.activate()
        template._raise_event(PolicyTemplateActivated(
            tenant_id=cmd.tenant_id, policy_id=cmd.policy_id
        ))
        await self._repo.save(template, expected_version=template.version)
        return template
