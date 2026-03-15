from dataspace_control_plane_core.domains._shared.errors import ValidationError

def require_counterparty(case: "NegotiationCase") -> None:
    if case.counterparty is None:
        raise ValidationError("NegotiationCase must have a counterparty before submitting an offer")

def require_active_entitlement(entitlement: "Entitlement") -> None:
    from datetime import datetime, timezone
    if not entitlement.is_active(datetime.now(timezone.utc)):
        raise ValidationError("Entitlement is not active", {"entitlement_id": str(entitlement.id)})
