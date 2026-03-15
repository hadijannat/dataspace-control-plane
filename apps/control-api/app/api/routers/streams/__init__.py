from fastapi import APIRouter
from app.api.routers.streams.workflows import router as workflows_router

router = APIRouter()
router.include_router(workflows_router, prefix="/workflows")
