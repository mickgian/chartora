"""PostgreSQL implementation of the ScoreRepository interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.domain.interfaces.repositories import ScoreRepository
from src.domain.models.entities import QuantumPowerScore
from src.infrastructure.database import ScoreTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.domain.models.value_objects import DateRange


class PgScoreRepository(ScoreRepository):
    """PostgreSQL-backed score repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest(self, company_id: int) -> QuantumPowerScore | None:
        result = await self._session.execute(
            select(ScoreTable)
            .where(ScoreTable.company_id == company_id)
            .order_by(ScoreTable.score_date.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_entity(row)

    async def get_latest_all(self) -> list[QuantumPowerScore]:
        """Get the most recent score for each company.

        Uses a subquery to find the max score_date per company,
        then joins to get the full score rows.
        """
        from sqlalchemy import func

        # Subquery: max score_date per company
        latest_dates = (
            select(
                ScoreTable.company_id,
                func.max(ScoreTable.score_date).label("max_date"),
            )
            .group_by(ScoreTable.company_id)
            .subquery()
        )

        result = await self._session.execute(
            select(ScoreTable).join(
                latest_dates,
                (ScoreTable.company_id == latest_dates.c.company_id)
                & (ScoreTable.score_date == latest_dates.c.max_date),
            )
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def get_by_date_range(
        self, company_id: int, date_range: DateRange
    ) -> list[QuantumPowerScore]:
        result = await self._session.execute(
            select(ScoreTable)
            .where(
                ScoreTable.company_id == company_id,
                ScoreTable.score_date >= date_range.start,
                ScoreTable.score_date <= date_range.end,
            )
            .order_by(ScoreTable.score_date)
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def save(self, score: QuantumPowerScore) -> QuantumPowerScore:
        row = ScoreTable(
            company_id=score.company_id,
            score_date=score.score_date,
            total_score=score.total_score,
            stock_momentum=score.stock_momentum,
            patent_velocity=score.patent_velocity,
            qubit_progress=score.qubit_progress,
            funding_strength=score.funding_strength,
            news_sentiment=score.news_sentiment,
            rank=score.rank,
            rank_change=score.rank_change,
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    async def save_many(
        self, scores: list[QuantumPowerScore]
    ) -> list[QuantumPowerScore]:
        if not scores:
            return []

        values = [
            {
                "company_id": s.company_id,
                "score_date": s.score_date,
                "total_score": s.total_score,
                "stock_momentum": s.stock_momentum,
                "patent_velocity": s.patent_velocity,
                "qubit_progress": s.qubit_progress,
                "funding_strength": s.funding_strength,
                "news_sentiment": s.news_sentiment,
                "rank": s.rank,
                "rank_change": s.rank_change,
            }
            for s in scores
        ]

        stmt = pg_insert(ScoreTable).values(values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_score_company_date",
            set_={
                "total_score": stmt.excluded.total_score,
                "stock_momentum": stmt.excluded.stock_momentum,
                "patent_velocity": stmt.excluded.patent_velocity,
                "qubit_progress": stmt.excluded.qubit_progress,
                "funding_strength": stmt.excluded.funding_strength,
                "news_sentiment": stmt.excluded.news_sentiment,
                "rank": stmt.excluded.rank,
                "rank_change": stmt.excluded.rank_change,
            },
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return scores

    @staticmethod
    def _to_entity(row: ScoreTable) -> QuantumPowerScore:
        return QuantumPowerScore(
            id=row.id,
            company_id=row.company_id,
            score_date=row.score_date,
            stock_momentum=float(row.stock_momentum),
            patent_velocity=float(row.patent_velocity),
            qubit_progress=float(row.qubit_progress),
            funding_strength=float(row.funding_strength),
            news_sentiment=float(row.news_sentiment),
            rank=row.rank,
            rank_change=row.rank_change,
        )
