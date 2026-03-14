"""PostgreSQL implementation of the PatentRepository interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from src.domain.interfaces.repositories import PatentRepository
from src.domain.models.entities import Patent
from src.domain.models.value_objects import DateRange, PatentSource
from src.infrastructure.database import PatentTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PgPatentRepository(PatentRepository):
    """PostgreSQL-backed patent repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_company(self, company_id: int) -> list[Patent]:
        result = await self._session.execute(
            select(PatentTable)
            .where(PatentTable.company_id == company_id)
            .order_by(PatentTable.filing_date.desc())
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def get_by_date_range(
        self, company_id: int, date_range: DateRange
    ) -> list[Patent]:
        result = await self._session.execute(
            select(PatentTable)
            .where(
                PatentTable.company_id == company_id,
                PatentTable.filing_date >= date_range.start,
                PatentTable.filing_date <= date_range.end,
            )
            .order_by(PatentTable.filing_date)
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def count_by_date_range(self, company_id: int, date_range: DateRange) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(PatentTable)
            .where(
                PatentTable.company_id == company_id,
                PatentTable.filing_date >= date_range.start,
                PatentTable.filing_date <= date_range.end,
            )
        )
        count: int = result.scalar_one()
        return count

    async def save(self, patent: Patent) -> Patent:
        row = PatentTable(
            company_id=patent.company_id,
            patent_number=patent.patent_number,
            title=patent.title,
            filing_date=patent.filing_date,
            source=patent.source.value,
            abstract=patent.abstract,
            grant_date=patent.grant_date,
            classification=patent.classification,
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    async def save_many(self, patents: list[Patent]) -> list[Patent]:
        rows = []
        for p in patents:
            row = PatentTable(
                company_id=p.company_id,
                patent_number=p.patent_number,
                title=p.title,
                filing_date=p.filing_date,
                source=p.source.value,
                abstract=p.abstract,
                grant_date=p.grant_date,
                classification=p.classification,
            )
            self._session.add(row)
            rows.append(row)
        await self._session.flush()
        return [self._to_entity(r) for r in rows]

    @staticmethod
    def _to_entity(row: PatentTable) -> Patent:
        return Patent(
            id=row.id,
            company_id=row.company_id,
            patent_number=row.patent_number,
            title=row.title,
            filing_date=row.filing_date,
            source=PatentSource(row.source),
            abstract=row.abstract,
            grant_date=row.grant_date,
            classification=row.classification,
        )
