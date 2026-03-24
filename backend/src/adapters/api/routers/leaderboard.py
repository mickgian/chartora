"""Leaderboard API endpoints."""

from __future__ import annotations

import logging
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

logger = logging.getLogger(__name__)

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
    sector: str | None = Query(
        default=None,
        description="Filter by sector: pure_play, big_tech, etf",
        pattern="^(pure_play|big_tech|etf)$",
    ),
) -> LeaderboardResponse:
    """Get the full leaderboard ranked by Quantum Power Score."""
    logger.info(
        "[LEADERBOARD] Fetching leaderboard sort_by=%s limit=%s",
        sort_by,
        limit,
    )

    # Fetch all latest scores
    scores = await score_repo.get_latest_all()
    if not scores:
        logger.warning(
            "[LEADERBOARD] No scores found in database — "
            "returning empty leaderboard. "
            "Has the data refresh pipeline been run?"
        )
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

    # Build company lookup, optionally filtered by sector
    if sector:
        companies = await company_repo.get_by_sector(sector)
    else:
        companies = await company_repo.get_all()
    company_map = {c.id: c for c in companies}

    # Filter scores to only include matching companies
    if sector:
        company_ids = set(company_map.keys())
        scores = [s for s in scores if s.company_id in company_ids]
        # Re-rank within the filtered set
        ranking_result = rank_companies(scores, metric=metric)

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

    logger.info(
        "[LEADERBOARD] Returning %d entries, latest_date=%s, sort_by=%s",
        len(entries),
        latest_date,
        sort_by,
    )

    # Metrics that currently use hardcoded/estimated data rather than live APIs
    # - patent_velocity: USPTO API domain migration, needs key after March 20
    # Funding now uses SEC EDGAR XBRL; qubits extracted from news via Claude
    hardcoded_metrics = [
        "patent_velocity",
    ]

    return LeaderboardResponse(
        metric=sort_by,
        entries=entries,
        count=len(entries),
        updated_at=updated_at,
        hardcoded_metrics=hardcoded_metrics,
        sector=sector,
    )
