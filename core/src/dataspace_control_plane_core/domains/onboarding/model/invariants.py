from dataspace_control_plane_core.domains._shared.errors import ValidationError
from .enums import OnboardingStatus
from .aggregates import OnboardingCase


def require_not_completed(case: OnboardingCase) -> None:
    """Raise ValidationError if the onboarding case is already completed."""
    if case.status == OnboardingStatus.COMPLETED:
        raise ValidationError(
            f"OnboardingCase {case.id} is already completed and cannot be modified."
        )
