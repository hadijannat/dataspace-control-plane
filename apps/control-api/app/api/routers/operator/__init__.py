from fastapi import APIRouter
from app.api.routers.operator.tenants import router as tenants_router
from app.api.routers.operator.procedures import router as procedures_router

router = APIRouter()
router.include_router(tenants_router, prefix="/tenants")
router.include_router(procedures_router, prefix="/procedures")
