from dataspace_control_plane_core.domains._shared.errors import DomainError, NotFoundError

class LegalEntityNotFoundError(NotFoundError):
    def __init__(self, tenant_id: str, legal_entity_id: str) -> None:
        super().__init__(f"LegalEntity {legal_entity_id} not found in tenant {tenant_id}")

class DuplicateLegalEntityError(DomainError):
    pass

class InvalidIdentifierSchemeError(DomainError):
    pass
