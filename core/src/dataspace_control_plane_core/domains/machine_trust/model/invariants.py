from dataspace_control_plane_core.domains._shared.errors import ValidationError

def require_did(participant: "TrustParticipant") -> None:
    if participant.did is None:
        raise ValidationError("TrustParticipant must have a DID before issuing credentials")
