from dataspace_control_plane_core.domains._shared.errors import ValidationError

def require_non_empty_subject(subject: str) -> None:
    if not subject.strip():
        raise ValidationError("Principal subject must not be blank")
