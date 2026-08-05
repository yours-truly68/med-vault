from uuid import UUID
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import LabMeasurement


class HealthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_measurements(
        self,
        user_id: UUID,
        family_member_id: UUID,
        *,
        test_name: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[LabMeasurement]:
        stmt = (
            select(LabMeasurement)
            .where(
                LabMeasurement.user_id == user_id,
                LabMeasurement.family_member_id == family_member_id,
            )
            .order_by(LabMeasurement.measured_at.asc().nullslast(), LabMeasurement.created_at.asc())
        )
        if test_name is not None:
            stmt = stmt.where(LabMeasurement.test_name.ilike(test_name))
        if from_date is not None:
            stmt = stmt.where(LabMeasurement.measured_at >= from_date)
        if to_date is not None:
            stmt = stmt.where(LabMeasurement.measured_at <= to_date)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
