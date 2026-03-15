"""Domain invariants for the twins domain."""
from __future__ import annotations

from dataspace_control_plane_core.domains._shared.errors import ValidationError
from .enums import TwinLifecycleState


def require_published(twin: object) -> None:
    """Raise ValidationError if the twin is not in the PUBLISHED lifecycle state."""
    from .aggregates import TwinAsset
    assert isinstance(twin, TwinAsset)
    if twin.lifecycle != TwinLifecycleState.PUBLISHED:
        raise ValidationError(
            f"TwinAsset {twin.id} must be published but is {twin.lifecycle.value}",
            {"twin_id": str(twin.id), "lifecycle": twin.lifecycle.value},
        )


def require_has_descriptor(twin: object) -> None:
    """Raise ValidationError if the twin has no descriptor attached."""
    from .aggregates import TwinAsset
    assert isinstance(twin, TwinAsset)
    if twin.descriptor is None:
        raise ValidationError(
            f"TwinAsset {twin.id} has no descriptor",
            {"twin_id": str(twin.id)},
        )
