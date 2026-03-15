from __future__ import annotations
from typing import Protocol
from dataspace_control_plane_core.domains._shared.ids import TenantId
from dataspace_control_plane_core.canonical_models.policy import CanonicalPolicy
from .model.aggregates import PolicyDecision


class PolicyTemplateRepository(Protocol):
    async def get(self, tenant_id: TenantId, policy_id: str) -> "PolicyTemplate": ...  # noqa: F821
    async def save(self, template: "PolicyTemplate", expected_version: int) -> None: ...  # noqa: F821


class PolicyDialectParser(Protocol):
    """Parses an external dialect (ODRL JSON-LD, Catena-X profile) into CanonicalPolicy."""
    def parse(self, raw: dict, dialect: str) -> CanonicalPolicy: ...


class PolicyDialectCompiler(Protocol):
    """Compiles CanonicalPolicy into a target dialect for wire/EDC use."""
    def compile(self, policy: CanonicalPolicy, dialect: str) -> dict: ...


class PolicyEvaluator(Protocol):
    """Evaluates a canonical policy against a context."""
    def evaluate(self, policy: CanonicalPolicy, action: str, subject: str, context: dict) -> bool: ...


class PurposeCatalogProvider(Protocol):
    async def list_purposes(self, namespace: str) -> list["PurposeCode"]: ...  # noqa: F821
