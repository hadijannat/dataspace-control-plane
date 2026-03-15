from fastapi import APIRouter
from app.api.routers.streams.tickets import router as tickets_router
from app.api.routers.streams.workflows import router as workflows_router

router = APIRouter()
router.include_router(tickets_router)
router.include_router(workflows_router, prefix="/workflows")
