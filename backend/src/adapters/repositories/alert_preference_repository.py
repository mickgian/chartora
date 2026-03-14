"""PostgreSQL implementation of the AlertPreferenceRepository interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from src.domain.interfaces.repositories import AlertPreferenceRepository
from src.domain.models.entities import AlertPreference
from src.infrastructure.database import AlertPreferenceTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PgAlertPreferenceRepository(AlertPreferenceRepository):
    """PostgreSQL-backed alert preference repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user(self, user_id: int) -> list[AlertPreference]:
        result = await self._session.execute(
            select(AlertPreferenceTable).where(AlertPreferenceTable.user_id == user_id)
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_enabled_by_type(self, alert_type: str) -> list[AlertPreference]:
        result = await self._session.execute(
            select(AlertPreferenceTable).where(
                AlertPreferenceTable.alert_type == alert_type,
                AlertPreferenceTable.enabled.is_(True),
            )
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def save(self, pref: AlertPreference) -> AlertPreference:
        if pref.id is not None:
            result = await self._session.execute(
                select(AlertPreferenceTable).where(AlertPreferenceTable.id == pref.id)
            )
            row = result.scalar_one_or_none()
            if row is not None:
                row.enabled = pref.enabled
                row.threshold = pref.threshold  # type: ignore[assignment]
                await self._session.flush()
                return self._to_entity(row)

        row = AlertPreferenceTable(
            user_id=pref.user_id,
            alert_type=pref.alert_type,
            enabled=pref.enabled,
            threshold=pref.threshold,  # type: ignore[arg-type]
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    async def delete(self, pref_id: int) -> None:
        await self._session.execute(
            delete(AlertPreferenceTable).where(AlertPreferenceTable.id == pref_id)
        )
        await self._session.flush()

    @staticmethod
    def _to_entity(row: AlertPreferenceTable) -> AlertPreference:
        return AlertPreference(
            id=row.id,
            user_id=row.user_id,
            alert_type=row.alert_type,
            enabled=row.enabled,
            threshold=float(row.threshold) if row.threshold is not None else None,
        )
