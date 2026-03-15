from __future__ import annotations
from dataspace_control_plane_core.domains._shared.errors import ValidationError


def require_minimum_identifiers(topology: "LegalEntityTopology") -> None:
    if not topology.external_identifiers:
        raise ValidationError(
            "LegalEntityTopology must have at least one external identifier before activation",
            {"legal_entity_id": str(topology.legal_entity_id)},
        )

    if not topology.display_name.strip():
        raise ValidationError(
            "LegalEntityTopology.display_name must not be blank",
            {"legal_entity_id": str(topology.legal_entity_id)},
        )
