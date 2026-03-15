from fastapi import APIRouter
from app.api.routers.public.procedures import router as procedures_router

router = APIRouter()
# Stable public automation/integration endpoints — separate from operator BFF DTOs.
router.include_router(procedures_router)
