from datetime import date
from uuid import UUID

from app.core.database.enums import TimelineEventType
from app.modules.timeline.repository import TimelineRepository
from app.modules.timeline.schemas import TimelineEventResponse, TimelineListResponse
from app.modules.users.models.models import User


class TimelineService:
    def __init__(self, repository: TimelineRepository) -> None:
        self._repository = repository

    async def list_events(
        self,
        user: User,
        *,
        family_member_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        event_type: TimelineEventType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> TimelineListResponse:
        events = await self._repository.list_events(
            user.id,
            family_member_id=family_member_id,
            from_date=from_date,
            to_date=to_date,
            event_type=event_type.value if event_type else None,
            limit=limit,
            offset=offset,
        )
        items = [
            TimelineEventResponse(
                id=event.id,
                document_id=event.document_id,
                family_member_id=event.family_member_id,
                event_date=event.event_date,
                event_type=TimelineEventType(event.event_type),
                title=event.title,
                description=event.description,
                source_field=event.source_field,
                document_type=event.document.document_type if event.document else None,
                original_filename=event.document.original_filename if event.document else None,
            )
            for event in events
        ]
        return TimelineListResponse(items=items, total=len(items))
