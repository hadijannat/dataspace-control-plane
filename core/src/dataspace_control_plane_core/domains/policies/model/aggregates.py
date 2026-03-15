from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId
from dataspace_control_plane_core.canonical_models.policy import CanonicalPolicy
from .enums import PolicySetStatus
from .value_objects import LossyClause, PurposeCode


@dataclass
class PolicyTemplate(AggregateRoot):
    """A reusable policy template authored by an operator."""
    name: str = ""
    description: str | None = None
    canonical_policy: CanonicalPolicy | None = None
    status: PolicySetStatus = PolicySetStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def activate(self) -> None:
        if self.canonical_policy is None:
            from dataspace_control_plane_core.domains._shared.errors import ValidationError
            raise ValidationError("PolicyTemplate has no canonical policy attached")
        if self.canonical_policy.needs_review:
            self.status = PolicySetStatus.NEEDS_REVIEW
        else:
            self.status = PolicySetStatus.ACTIVE

    def has_parse_losses(self) -> bool:
        return bool(self.canonical_policy and self.canonical_policy.parse_losses)


@dataclass
class PolicyDecision(AggregateRoot):
    """Records the outcome of a policy evaluation."""
    policy_id: str = ""
    subject: str = ""
    action: str = ""
    resource: str = ""
    allowed: bool = False
    reason: str = ""
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
