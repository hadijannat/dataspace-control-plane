"""Battery passport Annex XIII access matrix.

Constructs the AAS access matrix for the battery passport submodel, encoding
the four-tier access model from Annex XIII of Regulation (EU) 2023/1542.

The battery passport requirement (and therefore the full access matrix)
becomes effective from 2027-02-18.

Reference: Regulation (EU) 2023/1542, Annex XIII
"""
from __future__ import annotations

from ..._shared.implementation_profiles.aas_dpp4o.access_model import (
    AccessMatrix,
    AccessPermission,
)
from .authority_fields import AUTHORITY_FIELDS
from .legitimate_interest_fields import LEGITIMATE_INTEREST_FIELDS
from .public_fields import PUBLIC_FIELDS

# Battery passport obligation effective date (Regulation (EU) 2023/1542)
_EFFECTIVE_FROM = "2027-02-18"

# Manufacturer has full access — wildcard path covers all submodel elements
_MANUFACTURER_PATH = "**"

# Conditional path suffix for the implementing-act-gated legitimate-interest fields
_IMPLEMENTING_ACT_CONDITION = "legitimate_interest_verified"


def build_battery_access_matrix(version: str = "2023/1542") -> AccessMatrix:
    """Build the Annex XIII access matrix for the battery passport.

    Encodes four access tiers:
    - ``public``: read access to PUBLIC_FIELDS via QR scan / unique identifier
    - ``authority``: read access to AUTHORITY_FIELDS (market surveillance, customs)
    - ``legitimate_interest``: conditional read access to LEGITIMATE_INTEREST_FIELDS
        (implementing act pending under Article 74 §2 by 2026-08-18)
    - ``manufacturer``: full read/write access to all submodel elements

    Args:
        version: Regulation version string, defaults to "2023/1542".

    Returns:
        An AccessMatrix instance encoding all Annex XIII permissions.
    """
    permissions: list[AccessPermission] = []

    # Public access — anyone with QR/identifier
    for field in PUBLIC_FIELDS:
        permissions.append(
            AccessPermission(
                subject_class="public",
                path=f"BatteryPassport.{field}",
                kind="allow",
                effective_from=_EFFECTIVE_FROM,
            )
        )

    # Authority access — national market surveillance and customs
    for field in AUTHORITY_FIELDS:
        permissions.append(
            AccessPermission(
                subject_class="authority",
                path=f"BatteryPassport.{field}",
                kind="allow",
                effective_from=_EFFECTIVE_FROM,
            )
        )

    # Legitimate interest access — conditional on implementing act verification
    for field in LEGITIMATE_INTEREST_FIELDS:
        permissions.append(
            AccessPermission(
                subject_class="legitimate_interest",
                path=f"BatteryPassport.{field}",
                kind="conditional",
                condition=_IMPLEMENTING_ACT_CONDITION,
                effective_from=_EFFECTIVE_FROM,
            )
        )

    # Manufacturer — full access
    permissions.append(
        AccessPermission(
            subject_class="manufacturer",
            path=_MANUFACTURER_PATH,
            kind="allow",
            effective_from=_EFFECTIVE_FROM,
        )
    )

    return AccessMatrix(
        permissions=permissions,
        version=version,
        effective_from=_EFFECTIVE_FROM,
    )
