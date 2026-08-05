from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.database.enums import TimelineEventType
from app.core.dependencies.auth import CurrentUser
from app.modules.timeline.dependencies import TimelineServiceDep
from app.modules.timeline.schemas import TimelineListResponse

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("", response_model=TimelineListResponse)
async def list_timeline_events(
    current_user: CurrentUser,
    service: TimelineServiceDep,
    family_member_id: Annotated[UUID | None, Query()] = None,
    from_date: Annotated[date | None, Query()] = None,
    to_date: Annotated[date | None, Query()] = None,
    event_type: Annotated[TimelineEventType | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TimelineListResponse:
    return await service.list_events(
        current_user,
        family_member_id=family_member_id,
        from_date=from_date,
        to_date=to_date,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
