"""PostgreSQL implementation of the GovernmentContractRepository interface."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from src.domain.interfaces.repositories import GovernmentContractRepository
from src.domain.models.entities import GovernmentContract
from src.infrastructure.database import GovernmentContractTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PgGovernmentContractRepository(GovernmentContractRepository):
    """PostgreSQL-backed government contract repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_company(self, company_id: int) -> list[GovernmentContract]:
        result = await self._session.execute(
            select(GovernmentContractTable)
            .where(GovernmentContractTable.company_id == company_id)
            .order_by(GovernmentContractTable.amount.desc())
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def get_total_value(self, company_id: int) -> float:
        result = await self._session.execute(
            select(func.coalesce(func.sum(GovernmentContractTable.amount), 0)).where(
                GovernmentContractTable.company_id == company_id
            )
        )
        total = result.scalar_one()
        return float(total)

    async def save(self, contract: GovernmentContract) -> GovernmentContract:
        row = GovernmentContractTable(
            company_id=contract.company_id,
            award_id=contract.award_id,
            title=contract.title,
            amount=contract.amount,
            awarding_agency=contract.awarding_agency,
            start_date=contract.start_date,
            end_date=contract.end_date,
            description=contract.description,
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    async def save_many(
        self, contracts: list[GovernmentContract]
    ) -> list[GovernmentContract]:
        rows = []
        for c in contracts:
            row = GovernmentContractTable(
                company_id=c.company_id,
                award_id=c.award_id,
                title=c.title,
                amount=c.amount,
                awarding_agency=c.awarding_agency,
                start_date=c.start_date,
                end_date=c.end_date,
                description=c.description,
            )
            self._session.add(row)
            rows.append(row)
        await self._session.flush()
        return [self._to_entity(r) for r in rows]

    @staticmethod
    def _to_entity(row: GovernmentContractTable) -> GovernmentContract:
        return GovernmentContract(
            id=row.id,
            company_id=row.company_id,
            award_id=row.award_id,
            title=row.title,
            amount=Decimal(str(row.amount)),
            awarding_agency=row.awarding_agency,
            start_date=row.start_date,
            end_date=row.end_date,
            description=row.description,
        )
