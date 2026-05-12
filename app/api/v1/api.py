from fastapi import APIRouter
from app.api.v1.endpoints import meeting, history, status

api_router = APIRouter()

api_router.include_router(status.router, tags=["status"])
api_router.include_router(meeting.router, tags=["meeting"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
