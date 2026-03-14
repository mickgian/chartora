"""PostgreSQL implementation of the NewsRepository interface."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.domain.interfaces.repositories import NewsRepository
from src.domain.models.entities import NewsArticle
from src.domain.models.value_objects import DateRange, SentimentLabel
from src.infrastructure.database import NewsArticleTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PgNewsRepository(NewsRepository):
    """PostgreSQL-backed news article repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_company(
        self, company_id: int, limit: int = 20
    ) -> list[NewsArticle]:
        result = await self._session.execute(
            select(NewsArticleTable)
            .where(NewsArticleTable.company_id == company_id)
            .order_by(NewsArticleTable.published_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def get_by_date_range(
        self, company_id: int, date_range: DateRange
    ) -> list[NewsArticle]:
        result = await self._session.execute(
            select(NewsArticleTable)
            .where(
                NewsArticleTable.company_id == company_id,
                NewsArticleTable.published_at >= date_range.start,
                NewsArticleTable.published_at <= date_range.end,
            )
            .order_by(NewsArticleTable.published_at.desc())
        )
        rows = result.scalars().all()
        return [self._to_entity(row) for row in rows]

    async def save(self, article: NewsArticle) -> NewsArticle:
        row = NewsArticleTable(
            company_id=article.company_id,
            title=article.title,
            url=article.url,
            published_at=article.published_at,
            source_name=article.source_name,
            sentiment=article.sentiment.value if article.sentiment else None,
            sentiment_score=article.sentiment_score,
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    async def save_many(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        rows = []
        for a in articles:
            row = NewsArticleTable(
                company_id=a.company_id,
                title=a.title,
                url=a.url,
                published_at=a.published_at,
                source_name=a.source_name,
                sentiment=a.sentiment.value if a.sentiment else None,
                sentiment_score=a.sentiment_score,
            )
            self._session.add(row)
            rows.append(row)
        await self._session.flush()
        return [self._to_entity(r) for r in rows]

    @staticmethod
    def _to_entity(row: NewsArticleTable) -> NewsArticle:
        sentiment = None
        if row.sentiment:
            sentiment = SentimentLabel(row.sentiment)
        return NewsArticle(
            id=row.id,
            company_id=row.company_id,
            title=row.title,
            url=row.url,
            published_at=row.published_at,
            source_name=row.source_name,
            sentiment=sentiment,
            sentiment_score=(
                Decimal(str(row.sentiment_score))
                if row.sentiment_score is not None
                else None
            ),
        )
