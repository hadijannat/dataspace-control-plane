"""Error types for the packs layer."""
from __future__ import annotations


class PackError(Exception):
    """Root error for all pack-layer failures."""


class PackNotFoundError(PackError):
    """Requested pack ID is not registered."""


class PackConflictError(PackError):
    """Two active packs declare an incompatible constraint for the same target."""


class PackDependencyError(PackError):
    """A required pack dependency is missing or at an incompatible version."""


class PackVersionError(PackError):
    """Pack version string is malformed or incompatible with the declared range."""


class PackValidationError(PackError):
    """A rule, schema, or manifest failed validation."""


class PackActivationError(PackError):
    """Pack activation could not be completed (e.g. scope mismatch)."""


class PackProvenanceError(PackError):
    """An artifact was generated without a complete provenance record."""


class RuleNotFoundError(PackError):
    """A referenced rule_id does not exist in any active pack."""


class NormativeSourceError(PackError):
    """A required normative source file is missing or its checksum fails."""
