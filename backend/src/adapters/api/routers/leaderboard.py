"""Leaderboard API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Query

from src.adapters.api.dependencies import (  # noqa: TC001
    CompanyRepoDep,
    ScoreRepoDep,
)
from src.adapters.api.schemas import (
    CompanyResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    ScoreResponse,
)
from src.usecases.rank_companies import RankingMetric, rank_companies

router = APIRouter(prefix="/api/v1/leaderboard", tags=["leaderboard"])


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    company_repo: CompanyRepoDep,
    score_repo: ScoreRepoDep,
    sort_by: str = Query(
        default="total_score",
        description="Metric to sort by",
        pattern=(
            "^(total_score|stock_momentum"
            "|patent_velocity|qubit_progress"
            "|funding_strength|news_sentiment)$"
        ),
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=100,
        description="Top N companies",
    ),
) -> LeaderboardResponse:
    """Get the full leaderboard ranked by Quantum Power Score."""
    # Fetch all latest scores
    scores = await score_repo.get_latest_all()
    if not scores:
        return LeaderboardResponse(
            metric=sort_by,
            entries=[],
            count=0,
            updated_at=None,
        )

    # Rank by requested metric
    metric = RankingMetric(sort_by)
    ranking_result = rank_companies(scores, metric=metric)

    # Apply limit
    ranked = ranking_result.rankings
    if limit is not None:
        ranked = ranking_result.top(limit)

    # Build company lookup
    companies = await company_repo.get_all()
    company_map = {c.id: c for c in companies}

    entries: list[LeaderboardEntry] = []
    for rc in ranked:
        company = company_map.get(rc.company_id)
        if company is None:
            continue
        entries.append(
            LeaderboardEntry(
                rank=rc.rank,
                company=CompanyResponse(
                    id=company.id or 0,
                    name=company.name,
                    slug=company.slug,
                    sector=company.sector.value,
                    ticker=(company.ticker.symbol if company.ticker else None),
                    description=company.description,
                    is_etf=company.is_etf,
                    website=company.website,
                    logo_url=company.logo_url,
                ),
                score=ScoreResponse(
                    total_score=rc.score.total_score,
                    stock_momentum=rc.score.stock_momentum,
                    patent_velocity=rc.score.patent_velocity,
                    qubit_progress=rc.score.qubit_progress,
                    funding_strength=rc.score.funding_strength,
                    news_sentiment=rc.score.news_sentiment,
                    score_date=rc.score.score_date,
                    rank=rc.rank,
                    rank_change=rc.rank_change,
                ),
                trend=rc.trend.value,
                metric_value=rc.metric_value,
            )
        )

    # Determine latest update time
    latest_date = max(s.score_date for s in scores)
    updated_at = datetime.combine(latest_date, datetime.min.time(), tzinfo=UTC)

    return LeaderboardResponse(
        metric=sort_by,
        entries=entries,
        count=len(entries),
        updated_at=updated_at,
    )
