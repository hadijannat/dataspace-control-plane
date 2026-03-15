"""Tractus-X environment naming conventions and helper functions.

Keeps environment-specific naming out of general business logic.
"""
from __future__ import annotations

TRACTUSX_ENVIRONMENTS = frozenset({"dev", "int", "pre-prod", "prod"})


def connector_id(bpn: str, environment: str) -> str:
    """Return the conventional EDC connector ID for a BPN in a given environment.

    Example: connector_id("BPNL000000000001", "int") → "BPNL000000000001-int-edc"
    """
    return f"{bpn}-{environment}-edc"


def wallet_id(bpn: str) -> str:
    """Return the conventional Managed Identity Wallet ID for a BPN."""
    return f"wallet:{bpn}"


def default_task_queue(environment: str) -> str:
    """Return the Temporal task queue name for a given Tractus-X environment."""
    return f"onboarding-{environment}"


def is_valid_environment(environment: str) -> bool:
    """Return True if the environment name is a known Tractus-X environment."""
    return environment in TRACTUSX_ENVIRONMENTS


def registry_base_url(discovery_url: str, bpn: str) -> str:
    """Compose the expected AAS Registry URL for a BPN using Tractus-X conventions.

    In practice the AAS Registry URL is discovered via the Discovery Service;
    this helper provides a fallback convention for known environments.
    """
    return f"{discovery_url.rstrip('/')}/registry/{bpn}"
