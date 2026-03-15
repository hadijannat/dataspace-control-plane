"""Public import surface for the twins domain."""
from .model.enums import TwinVisibility, TwinLifecycleState, SubmodelCategory
from .model.value_objects import TwinDescriptor, TwinVersion, EndpointHealth
from .model.aggregates import (
    AasShellRecord,
    RegistryEntryRef,
    SemanticBinding,
    SubmodelBinding,
    TwinAccessPolicyBinding,
    TwinAsset,
    TwinPublication,
)
from .model.invariants import require_published, require_has_descriptor
from .commands import (
    RegisterTwinCommand,
    PublishTwinCommand,
    UpdateTwinDescriptorCommand,
    DeprecateTwinCommand,
    WithdrawTwinCommand,
)
from .events import (
    TwinRegistered,
    TwinPublished,
    TwinDescriptorUpdated,
    TwinDeprecated,
    TwinWithdrawn,
)
from .errors import (
    TwinNotFoundError,
    DuplicateTwinError,
    TwinNotPublishedError,
    TwinEndpointUnreachableError,
)
from .ports import TwinRepository, AasRegistryPort, TwinEndpointProbePort
from .services import TwinPublicationService

__all__ = [
    # enums
    "TwinVisibility",
    "TwinLifecycleState",
    "SubmodelCategory",
    # value objects
    "TwinDescriptor",
    "TwinVersion",
    "EndpointHealth",
    "AasShellRecord",
    "SubmodelBinding",
    "TwinPublication",
    "RegistryEntryRef",
    "TwinAccessPolicyBinding",
    "SemanticBinding",
    # aggregates
    "TwinAsset",
    # invariants
    "require_published",
    "require_has_descriptor",
    # commands
    "RegisterTwinCommand",
    "PublishTwinCommand",
    "UpdateTwinDescriptorCommand",
    "DeprecateTwinCommand",
    "WithdrawTwinCommand",
    # events
    "TwinRegistered",
    "TwinPublished",
    "TwinDescriptorUpdated",
    "TwinDeprecated",
    "TwinWithdrawn",
    # errors
    "TwinNotFoundError",
    "DuplicateTwinError",
    "TwinNotPublishedError",
    "TwinEndpointUnreachableError",
    # ports
    "TwinRepository",
    "AasRegistryPort",
    "TwinEndpointProbePort",
    # services
    "TwinPublicationService",
]
