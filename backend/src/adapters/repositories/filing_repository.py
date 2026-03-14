"""PostgreSQL implementation of the FilingRepository interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from src.domain.interfaces.repositories import FilingRepository
from src.domain.models.entities import Filing
from src.domain.models.value_objects import FilingType
from src.infrastructure.database import FilingTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PgFilingRepository(FilingRepository):
    """PostgreSQL-backed filing repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_company(self, company_id: int) -> list[Filing]:
        result = await self._session.execute(
            select(FilingTable)
            .where(FilingTable.company_id == company_id)
            .order_by(FilingTable.filing_date.desc())
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def get_by_type(self, company_id: int, filing_type: str) -> list[Filing]:
        result = await self._session.execute(
            select(FilingTable)
            .where(
                FilingTable.company_id == company_id,
                FilingTable.filing_type == filing_type,
            )
            .order_by(FilingTable.filing_date.desc())
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def save(self, filing: Filing) -> Filing:
        row = FilingTable(
            company_id=filing.company_id,
            filing_type=filing.filing_type.value,
            filing_date=filing.filing_date,
            description=filing.description,
            url=filing.url,
            data_json=filing.data_json,
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    async def save_many(self, filings: list[Filing]) -> list[Filing]:
        rows = []
        for f in filings:
            row = FilingTable(
                company_id=f.company_id,
                filing_type=f.filing_type.value,
                filing_date=f.filing_date,
                description=f.description,
                url=f.url,
                data_json=f.data_json,
            )
            self._session.add(row)
            rows.append(row)
        await self._session.flush()
        return [self._to_entity(r) for r in rows]

    @staticmethod
    def _to_entity(row: FilingTable) -> Filing:
        return Filing(
            id=row.id,
            company_id=row.company_id,
            filing_type=FilingType(row.filing_type),
            filing_date=row.filing_date,
            description=row.description,
            url=row.url,
            data_json=row.data_json,
        )
