"""Catena-X procedure hooks.

Injects Catena-X-specific validation and context augmentation at procedure
lifecycle points. All hooks are synchronous and deterministic — no I/O.

Reference: Catena-X Operating Model v4.0
"""
from __future__ import annotations

from typing import Any

from .identifiers import BpnlSchemeProvider, BpnValidator

_bpnl_scheme = BpnlSchemeProvider()


class CatenaxProcedureHooks:
    """ProcedureHookProvider for Catena-X lifecycle points."""

    def on_onboarding(self, context: dict[str, Any]) -> dict[str, Any]:
        """Validate BPNL presence and flag governance check requirement.

        Raises:
            ValueError: If ``bpnl`` is missing or invalid in ``context``.
        """
        augmented = dict(context)

        bpnl = context.get("bpnl", "")
        if not bpnl:
            raise ValueError(
                "Catena-X onboarding requires a 'bpnl' field in context."
            )
        if not _bpnl_scheme.validate(bpnl):
            raise ValueError(
                f"Catena-X onboarding: 'bpnl' value {bpnl!r} is not a valid BPNL identifier."
            )

        augmented["cx_governance_check_required"] = True
        return augmented

    def on_negotiation(self, context: dict[str, Any]) -> dict[str, Any]:
        """Validate counterparty BPN and flag membership check requirement.

        Raises:
            ValueError: If ``counterparty_bpn`` is present but invalid.
        """
        augmented = dict(context)

        counterparty_bpn = context.get("counterparty_bpn", "")
        if counterparty_bpn and not BpnValidator.is_valid_bpn(
            counterparty_bpn.upper()
        ):
            raise ValueError(
                f"Catena-X negotiation: counterparty_bpn {counterparty_bpn!r} "
                "is not a valid BPN identifier."
            )

        augmented["cx_membership_check_required"] = True
        return augmented

    def on_publishing(self, context: dict[str, Any]) -> dict[str, Any]:
        """Validate that the asset has a cx_offer_policy field and set profile.

        Raises:
            ValueError: If ``cx_offer_policy`` is missing from ``context``.
        """
        augmented = dict(context)

        if "cx_offer_policy" not in context:
            raise ValueError(
                "Catena-X publishing requires a 'cx_offer_policy' field in context."
            )

        augmented["cx_policy_profile"] = "catenax"
        return augmented

    def on_evidence_export(self, context: dict[str, Any]) -> dict[str, Any]:
        """Stamp evidence export with Catena-X version."""
        augmented = dict(context)
        augmented["cx_evidence_version"] = "4.0"
        return augmented
