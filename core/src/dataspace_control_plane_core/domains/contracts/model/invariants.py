from dataspace_control_plane_core.domains._shared.errors import ValidationError
from dataspace_control_plane_core.domains._shared.time import utc_now

def require_counterparty(case: "NegotiationCase") -> None:
    if case.counterparty is None:
        raise ValidationError("NegotiationCase must have a counterparty before submitting an offer")

def require_active_entitlement(entitlement: "Entitlement") -> None:
    if not entitlement.is_active(utc_now()):
        raise ValidationError("Entitlement is not active", {"entitlement_id": str(entitlement.id)})
