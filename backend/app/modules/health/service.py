from datetime import date
from uuid import UUID

from app.modules.family_members.exceptions import FamilyMemberNotFoundError
from app.modules.family_members.repository import FamilyMemberRepository
from app.modules.health.repository import HealthRepository
from app.modules.health.schemas import (
    HealthTrendPoint,
    HealthTrendSeries,
    HealthTrendsResponse,
)
from app.modules.users.models.models import User


class HealthService:
    def __init__(
        self,
        repository: HealthRepository,
        family_members: FamilyMemberRepository,
    ) -> None:
        self._repository = repository
        self._family_members = family_members

    async def get_health_trends(
        self,
        user: User,
        family_member_id: UUID,
        *,
        test_name: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> HealthTrendsResponse:
        member = await self._family_members.get_by_id_and_user_id(
            family_member_id,
            user.id,
        )
        if member is None:
            raise FamilyMemberNotFoundError()

        measurements = await self._repository.list_measurements(
            user.id,
            family_member_id,
            test_name=test_name,
            from_date=from_date,
            to_date=to_date,
        )

        grouped: dict[str, HealthTrendSeries] = {}
        for measurement in measurements:
            if measurement.measured_at is None:
                continue
            key = measurement.test_name.strip().lower()
            if key not in grouped:
                grouped[key] = HealthTrendSeries(
                    test_name=measurement.test_name,
                    unit=measurement.unit,
                )
            grouped[key].points.append(
                HealthTrendPoint(
                    date=measurement.measured_at,
                    value=float(measurement.value),
                    unit=measurement.unit,
                    reference_low=(
                        float(measurement.reference_low)
                        if measurement.reference_low is not None
                        else None
                    ),
                    reference_high=(
                        float(measurement.reference_high)
                        if measurement.reference_high is not None
                        else None
                    ),
                    document_id=measurement.document_id,
                )
            )

        series = sorted(grouped.values(), key=lambda item: item.test_name.lower())
        return HealthTrendsResponse(
            family_member_id=family_member_id,
            series=series,
            total_measurements=len(measurements),
        )
