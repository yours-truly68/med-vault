from fastapi import APIRouter, Depends

from app.core.config.settings import Settings
from app.core.database.session import Database
from app.core.dependencies.database import get_app_settings, get_database
from app.shared.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_app_settings),
    database: Database = Depends(get_database),
) -> HealthResponse:
    db_connected = await database.ping()
    return HealthResponse(
        status="ok" if db_connected else "degraded",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        database="connected" if db_connected else "disconnected",
    )
