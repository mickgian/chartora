"""PostgreSQL implementation of the CompanyRepository interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from src.domain.interfaces.repositories import CompanyRepository
from src.domain.models.entities import Company
from src.domain.models.value_objects import Sector, Ticker
from src.infrastructure.database import CompanyTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PgCompanyRepository(CompanyRepository):
    """PostgreSQL-backed company repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, company_id: int) -> Company | None:
        result = await self._session.execute(
            select(CompanyTable).where(CompanyTable.id == company_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    async def get_by_slug(self, slug: str) -> Company | None:
        result = await self._session.execute(
            select(CompanyTable).where(CompanyTable.slug == slug)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    async def get_all(self) -> list[Company]:
        result = await self._session.execute(
            select(CompanyTable).order_by(CompanyTable.name)
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def get_by_sector(self, sector: str) -> list[Company]:
        result = await self._session.execute(
            select(CompanyTable)
            .where(CompanyTable.sector == sector)
            .order_by(CompanyTable.name)
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def save(self, company: Company) -> Company:
        if company.id is not None:
            # Update existing
            result = await self._session.execute(
                select(CompanyTable).where(CompanyTable.id == company.id)
            )
            row = result.scalar_one_or_none()
            if row is not None:
                row.name = company.name
                row.slug = company.slug
                row.ticker = company.ticker.symbol if company.ticker else None
                row.description = company.description
                row.sector = company.sector.value
                row.is_etf = company.is_etf
                row.website = company.website
                row.logo_url = company.logo_url
                await self._session.flush()
                return self._to_entity(row)

        # Insert new
        row = CompanyTable(
            name=company.name,
            slug=company.slug,
            ticker=company.ticker.symbol if company.ticker else None,
            description=company.description,
            sector=company.sector.value,
            is_etf=company.is_etf,
            website=company.website,
            logo_url=company.logo_url,
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    async def delete(self, company_id: int) -> None:
        await self._session.execute(
            delete(CompanyTable).where(CompanyTable.id == company_id)
        )
        await self._session.flush()

    @staticmethod
    def _to_entity(row: CompanyTable) -> Company:
        """Convert ORM row to domain entity."""
        return Company(
            id=row.id,
            name=row.name,
            slug=row.slug,
            sector=Sector(row.sector),
            ticker=Ticker(row.ticker) if row.ticker else None,
            description=row.description,
            is_etf=row.is_etf,
            website=row.website,
            logo_url=row.logo_url,
        )
