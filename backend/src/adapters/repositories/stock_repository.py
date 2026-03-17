"""PostgreSQL implementation of the StockRepository interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.domain.interfaces.repositories import StockRepository
from src.domain.models.entities import StockPrice
from src.infrastructure.database import StockPriceTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.domain.models.value_objects import DateRange


class PgStockRepository(StockRepository):
    """PostgreSQL-backed stock price repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest(self, company_id: int) -> StockPrice | None:
        result = await self._session.execute(
            select(StockPriceTable)
            .where(StockPriceTable.company_id == company_id)
            .order_by(StockPriceTable.price_date.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    async def get_by_date_range(
        self, company_id: int, date_range: DateRange
    ) -> list[StockPrice]:
        result = await self._session.execute(
            select(StockPriceTable)
            .where(
                StockPriceTable.company_id == company_id,
                StockPriceTable.price_date >= date_range.start,
                StockPriceTable.price_date <= date_range.end,
            )
            .order_by(StockPriceTable.price_date)
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def get_all_for_company(self, company_id: int) -> list[StockPrice]:
        result = await self._session.execute(
            select(StockPriceTable)
            .where(StockPriceTable.company_id == company_id)
            .order_by(StockPriceTable.price_date)
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def save(self, stock_price: StockPrice) -> StockPrice:
        row = StockPriceTable(
            company_id=stock_price.company_id,
            price_date=stock_price.price_date,
            close_price=stock_price.close_price,
            open_price=stock_price.open_price,
            high_price=stock_price.high_price,
            low_price=stock_price.low_price,
            volume=stock_price.volume,
            market_cap=stock_price.market_cap,
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    async def save_many(self, stock_prices: list[StockPrice]) -> list[StockPrice]:
        if not stock_prices:
            return []

        values = [
            {
                "company_id": sp.company_id,
                "price_date": sp.price_date,
                "close_price": sp.close_price,
                "open_price": sp.open_price,
                "high_price": sp.high_price,
                "low_price": sp.low_price,
                "volume": sp.volume,
                "market_cap": sp.market_cap,
            }
            for sp in stock_prices
        ]

        stmt = pg_insert(StockPriceTable).values(values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_stock_company_date",
            set_={
                "close_price": stmt.excluded.close_price,
                "open_price": stmt.excluded.open_price,
                "high_price": stmt.excluded.high_price,
                "low_price": stmt.excluded.low_price,
                "volume": stmt.excluded.volume,
                "market_cap": stmt.excluded.market_cap,
            },
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return stock_prices

    @staticmethod
    def _to_entity(row: StockPriceTable) -> StockPrice:
        return StockPrice(
            id=row.id,
            company_id=row.company_id,
            price_date=row.price_date,
            close_price=row.close_price,
            open_price=row.open_price,
            high_price=row.high_price,
            low_price=row.low_price,
            volume=row.volume,
            market_cap=row.market_cap,
        )
