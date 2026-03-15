"""Protocol-style interfaces for pack capabilities.

Each interface is defined as a typing.Protocol so that packs can implement
any subset without inheriting from a base class. The registry resolves
packs by capability at runtime using isinstance() against these protocols.

Conventions:
- Methods return plain Python dicts or typed dataclasses — never raw
  adapter types, ORM models, or Temporal SDK objects.
- Methods are synchronous (packs are rule/data processors, not I/O performers).
- Every method that produces an artifact must accept an ``activation_scope``
  parameter so provenance can be stamped.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Protocol, runtime_checkable

from .rule_model import RuleDefinition, ValidationResult


@runtime_checkable
class RequirementProvider(Protocol):
    """Provides the set of normative requirements for a given context."""

    def requirements(
        self,
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return all active requirements applicable to ``context`` on ``on``."""
        ...

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],
        on: date | None = None,
    ) -> ValidationResult:
        """Validate ``subject`` against all active requirements."""
        ...


@runtime_checkable
class PolicyDialectProvider(Protocol):
    """Compiles and parses policies in an ecosystem-specific dialect."""

    dialect_id: str
    """Unique identifier for this policy dialect (e.g. ``catenax``, ``gaiax``)."""

    def compile(
        self,
        canonical_policy: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Compile a canonical policy into the dialect's representation."""
        ...

    def parse(self, dialect_policy: dict[str, Any]) -> dict[str, Any]:
        """Parse a dialect-specific policy back to a canonical policy dict."""
        ...


@runtime_checkable
class PurposeCatalogProvider(Protocol):
    """Provides the purpose vocabulary for a policy dialect."""

    def purposes(self) -> list[dict[str, Any]]:
        """Return all declared purposes with id, label, and normative reference."""
        ...

    def resolve_purpose(self, purpose_id: str) -> dict[str, Any] | None:
        """Return a single purpose definition or None if unknown."""
        ...


@runtime_checkable
class IdentifierSchemeProvider(Protocol):
    """Validates and generates identifiers in an ecosystem-specific scheme."""

    scheme_id: str
    """Unique scheme identifier (e.g. ``bpnl``, ``eori``, ``gs1``)."""

    def validate(self, value: str) -> bool:
        """Return True if ``value`` is a valid identifier in this scheme."""
        ...

    def normalize(self, value: str) -> str:
        """Return the canonical normalized form of the identifier."""
        ...


@runtime_checkable
class CredentialProfileProvider(Protocol):
    """Maps canonical identity/credential models to ecosystem VC structures."""

    def required_credentials(self, *, context: dict[str, Any]) -> list[str]:
        """Return required credential type names for the given context."""
        ...

    def build_vc_payload(
        self,
        credential_type: str,
        subject: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Build a VC payload dict for ``credential_type`` from ``subject``."""
        ...


@runtime_checkable
class TrustAnchorOverlayProvider(Protocol):
    """Provides a federation-specific overlay on the base trust anchor set."""

    def overlay_anchors(
        self, base_anchors: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Filter or augment ``base_anchors`` for this federation/ecosystem."""
        ...


@runtime_checkable
class TwinTemplateProvider(Protocol):
    """Provides AAS twin templates for a given ecosystem/regulation context."""

    def templates(self, *, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Return twin template descriptors applicable to ``context``."""
        ...

    def apply_template(
        self,
        template_id: str,
        subject: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Instantiate a template with ``subject`` data."""
        ...


@runtime_checkable
class ProcedureHookProvider(Protocol):
    """Injects pack-specific logic at procedure lifecycle points.

    Hooks are invoked by procedure activities (not by workflows directly)
    and must be synchronous and deterministic.
    """

    def on_onboarding(self, context: dict[str, Any]) -> dict[str, Any]:
        """Called during company/connector onboarding. Returns augmented context."""
        ...

    def on_negotiation(self, context: dict[str, Any]) -> dict[str, Any]:
        """Called at contract negotiation start. Returns augmented context."""
        ...

    def on_publishing(self, context: dict[str, Any]) -> dict[str, Any]:
        """Called when an asset is published. Returns augmented context."""
        ...

    def on_evidence_export(self, context: dict[str, Any]) -> dict[str, Any]:
        """Called during evidence export. Returns augmented evidence dict."""
        ...


@runtime_checkable
class EvidenceAugmenter(Protocol):
    """Augments an evidence bundle with pack-specific fields."""

    def augment(
        self,
        evidence: dict[str, Any],
        *,
        activation_scope: str,
    ) -> dict[str, Any]:
        """Add pack-specific evidence fields. Must not remove existing fields."""
        ...


@runtime_checkable
class UiSchemaProvider(Protocol):
    """Provides JSON Schema-compatible UI metadata for operator dashboards."""

    def ui_schema(self, *, locale: str = "en") -> dict[str, Any]:
        """Return a UI schema dict for this pack's configuration."""
        ...


@runtime_checkable
class PackMigrationProvider(Protocol):
    """Handles migrating activation data between pack versions."""

    def migrate(
        self,
        activation_data: dict[str, Any],
        *,
        from_version: str,
        to_version: str,
    ) -> dict[str, Any]:
        """Migrate ``activation_data`` from ``from_version`` to ``to_version``."""
        ...


@runtime_checkable
class DataExchangeProfileProvider(Protocol):
    """Declares which data exchange capabilities are supported/required."""

    def supported_protocols(self) -> list[str]:
        """Return protocol identifiers (e.g. ``dsp``, ``dcp``, ``opc-ua``)."""
        ...

    def required_capabilities(self, *, context: dict[str, Any]) -> list[str]:
        """Return capability names required in the given context."""
        ...


@runtime_checkable
class LifecycleModelProvider(Protocol):
    """Defines valid lifecycle states and transition rules for an artifact type."""

    def states(self) -> list[str]:
        """Return all valid state names."""
        ...

    def transitions(self) -> list[dict[str, Any]]:
        """Return allowed transitions as {from, to, trigger, conditions}."""
        ...

    def validate_transition(
        self,
        current_state: str,
        target_state: str,
        *,
        context: dict[str, Any],
    ) -> ValidationResult:
        ...
