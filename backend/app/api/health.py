from fastapi import APIRouter, Depends, Request

from app.core.config.settings import Settings
from app.core.database.session import Database
from app.core.dependencies.database import get_app_settings, get_database
from app.queue.interface import IJobQueue
from app.shared.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    database: Database = Depends(get_database),
) -> HealthResponse:
    db_connected = await database.ping()
    
    redis_status = "disconnected"
    queue_status = "disconnected"
    worker_status = "unregistered"

    job_queue: IJobQueue | None = getattr(request.app.state, "job_queue", None)
    if job_queue is not None:
        q_health = await job_queue.health_check()
        redis_status = "connected" if q_health.get("redis_connected") else "disconnected"
        queue_status = "connected" if q_health.get("queue_connected") else "disconnected"
        worker_status = "registered" if q_health.get("worker_registered") else "unregistered"

    overall_ok = db_connected and redis_status == "connected"

    return HealthResponse(
        status="ok" if overall_ok else "degraded",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        database="connected" if db_connected else "disconnected",
        redis=redis_status,
        queue=queue_status,
        worker=worker_status,
    )
