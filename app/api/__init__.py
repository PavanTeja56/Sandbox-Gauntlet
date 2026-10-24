from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.runs import router as runs_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(runs_router, prefix="/api", tags=["Runs"])
