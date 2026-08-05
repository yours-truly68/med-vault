from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies.auth import CurrentUser
from app.modules.health.dependencies import HealthServiceDep
from app.modules.health.schemas import HealthTrendsResponse

router = APIRouter(prefix="/family-members", tags=["health"])


@router.get("/{member_id}/health-trends", response_model=HealthTrendsResponse)
async def get_health_trends(
    member_id: UUID,
    current_user: CurrentUser,
    service: HealthServiceDep,
    test_name: Annotated[str | None, Query()] = None,
    from_date: Annotated[date | None, Query()] = None,
    to_date: Annotated[date | None, Query()] = None,
) -> HealthTrendsResponse:
    return await service.get_health_trends(
        current_user,
        member_id,
        test_name=test_name,
        from_date=from_date,
        to_date=to_date,
    )
