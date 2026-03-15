from dataspace_control_plane_core.domains._shared.errors import ValidationError

def require_clean_policy_for_activation(template: "PolicyTemplate") -> None:
    if template.has_parse_losses():
        raise ValidationError(
            "PolicyTemplate with lossy parse clauses cannot be activated without review",
            {"policy_id": str(template.id)}
        )
