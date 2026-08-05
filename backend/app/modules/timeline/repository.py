from uuid import UUID
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.documents.models import Document, TimelineEvent


class TimelineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_events(
        self,
        user_id: UUID,
        *,
        family_member_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TimelineEvent]:
        stmt = (
            select(TimelineEvent)
            .options(selectinload(TimelineEvent.document))
            .where(TimelineEvent.user_id == user_id)
            .order_by(TimelineEvent.event_date.desc(), TimelineEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if family_member_id is not None:
            stmt = stmt.where(TimelineEvent.family_member_id == family_member_id)
        if from_date is not None:
            stmt = stmt.where(TimelineEvent.event_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(TimelineEvent.event_date <= to_date)
        if event_type is not None:
            stmt = stmt.where(TimelineEvent.event_type == event_type)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
