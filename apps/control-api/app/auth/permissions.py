from fastapi import Depends, HTTPException, status
from app.auth.principals import Principal
from app.api.deps.auth import get_current_principal


def require_role(role: str):
    """FastAPI dependency: gate on a realm or client role."""
    async def _check(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not principal.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return principal
    return _check


def require_tenant_access(tenant_id_param: str = "tenant_id"):
    """FastAPI dependency: gate on tenant membership."""
    async def _check(
        tenant_id: str,
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if not principal.can_access_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this tenant is not permitted",
            )
        return principal
    return _check
