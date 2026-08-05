from fastapi import APIRouter

from app.api.health import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.chat.router import router as chat_router
from app.modules.documents.router import router as documents_router
from app.modules.family_members.router import router as family_members_router
from app.modules.health.router import router as health_trends_router
from app.modules.processing.router import router as processing_router
from app.modules.search.router import router as search_router
from app.modules.timeline.router import router as timeline_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(family_members_router)
api_router.include_router(health_trends_router)
api_router.include_router(documents_router)
api_router.include_router(processing_router)
api_router.include_router(search_router)
api_router.include_router(chat_router)
api_router.include_router(timeline_router)
