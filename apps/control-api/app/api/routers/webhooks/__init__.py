from fastapi import APIRouter
from app.api.routers.webhooks.management import router as management_router

router = APIRouter()
# Inbound webhooks from external systems (EDC, Keycloak events, etc.)
router.include_router(management_router)
