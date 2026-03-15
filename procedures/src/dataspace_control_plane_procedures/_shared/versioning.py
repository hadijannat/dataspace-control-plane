"""Workflow versioning helpers — patch ID registry.

Usage in workflow code (call only inside workflow context):
    from temporalio import workflow
    from dataspace_control_plane_procedures._shared.versioning import patched

    if patched("company_onboarding.v2_add_hierarchy_phase"):
        # new code path
    else:
        # old code path
"""
from temporalio import workflow

# Registry of patch IDs used across all procedures.
# Format: "<procedure_slug>.<short_description>"
PATCH_IDS: dict[str, str] = {
    "company_onboarding.v2_hierarchy_phase": "company_onboarding_v2_hierarchy_phase",
    "connector_bootstrap.v2_health_check": "connector_bootstrap_v2_health_check",
    "wallet_bootstrap.v2_reissue_support": "wallet_bootstrap_v2_reissue_support",
    "negotiate_contract.v2_counteroffer": "negotiate_contract_v2_counteroffer",
    "rotate_credentials.v2_wallet_rebind": "rotate_credentials_v2_wallet_rebind",
}


def patched(patch_key: str) -> bool:
    """Return True if new code path should run. Must be called in workflow context."""
    patch_id = PATCH_IDS.get(patch_key)
    if patch_id is None:
        raise KeyError(f"Unknown patch key: {patch_key!r}. Register it in PATCH_IDS first.")
    return workflow.patched(patch_id)
