"""
Tenant context: validates that the authenticated principal has access to the requested tenant.

Provides two complementary dependency styles:
- `require_tenant(tenant_id)` — factory returning a dependency for a fixed tenant_id value.
- `TenantScope` — callable class that reads `tenant_id` from a path/query parameter by name.
"""
from typing import Callable

from fastapi import Depends, HTTPException, Request, status

from app.api.deps.auth import get_current_principal
from app.auth.principals import Principal


def require_tenant(tenant_id: str) -> Callable[..., str]:
    """
    Return a FastAPI dependency that validates tenant access for a given fixed tenant_id string.

    Usage::

        @router.post("/tenants/{tenant_id}/things")
        async def create_thing(
            tenant_id: str = Depends(require_tenant("acme")),
        ) -> ...:
            ...

    Raises 403 if the authenticated principal does not have access to `tenant_id`.
    Returns the tenant_id string on success so it can be used inline.
    """

    async def _dep(principal: Principal = Depends(get_current_principal)) -> str:
        if not principal.can_access_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to tenant '{tenant_id}' is not permitted",
            )
        return tenant_id

    return _dep


class TenantScope:
    """
    Callable FastAPI dependency for tenant access checks.

    Reads the tenant_id from a named path or query parameter (default: ``"tenant_id"``)
    and verifies that the authenticated principal has access to it.

    Usage::

        tenant_scope = TenantScope()

        @router.get("/tenants/{tenant_id}/procedures")
        async def list_procedures(
            tenant_id: str = Depends(tenant_scope),
        ) -> ...:
            ...

    Raises 403 if access is denied; returns the resolved tenant_id string on success.
    """

    def __init__(self, tenant_id_param: str = "tenant_id") -> None:
        self.tenant_id_param = tenant_id_param

    async def __call__(
        self,
        request: Request,
        principal: Principal = Depends(get_current_principal),
    ) -> str:
        """
        Validate that the principal has access to the requested tenant_id.

        The tenant_id is extracted from request path parameters first, then query
        parameters, using the configured ``tenant_id_param`` name.
        Raises HTTP 403 if the principal is not authorised; returns the tenant_id otherwise.
        """
        tenant_id: str | None = request.path_params.get(self.tenant_id_param)
        if tenant_id is None:
            tenant_id = request.query_params.get(self.tenant_id_param)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required parameter: '{self.tenant_id_param}'",
            )
        if not principal.can_access_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to tenant '{tenant_id}' is not permitted",
            )
        return tenant_id
