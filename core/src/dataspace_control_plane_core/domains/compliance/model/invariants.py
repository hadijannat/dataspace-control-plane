from dataspace_control_plane_core.domains._shared.errors import ValidationError
from .value_objects import ScanScope


def require_non_empty_scope(scope: ScanScope) -> None:
    """Raise ValidationError if the scan scope contains no frameworks."""
    if not scope.frameworks:
        raise ValidationError(
            "ScanScope must specify at least one compliance framework."
        )
