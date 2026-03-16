"""Rankings API endpoints — companies ranked by individual metrics."""

from __future__ import annotations

from fastapi import APIRouter

from src.adapters.api.dependencies import (  # noqa: TC001
    CompanyRepoDep,
    GovContractRepoDep,
    ScoreRepoDep,
)
from src.adapters.api.schemas import (
    CompanyResponse,
    RankingEntry,
    RankingResponse,
)
from src.usecases.rank_companies import (
    RankingMetric,
    rank_companies,
)

router = APIRouter(prefix="/api/v1/rankings", tags=["rankings"])


async def _build_ranking(
    metric: RankingMetric,
    company_repo: CompanyRepoDep,
    score_repo: ScoreRepoDep,
) -> RankingResponse:
    """Shared logic for all ranking endpoints."""
    scores = await score_repo.get_latest_all()
    if not scores:
        return RankingResponse(metric=metric.value, entries=[], count=0)

    result = rank_companies(scores, metric=metric)

    companies = await company_repo.get_all()
    company_map = {c.id: c for c in companies}

    entries: list[RankingEntry] = []
    for rc in result.rankings:
        company = company_map.get(rc.company_id)
        if company is None:
            continue
        entries.append(
            RankingEntry(
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
                metric_value=rc.metric_value,
                trend=rc.trend.value,
            )
        )

    return RankingResponse(
        metric=metric.value,
        entries=entries,
        count=len(entries),
    )


@router.get("/patents", response_model=RankingResponse)
async def get_patent_rankings(
    company_repo: CompanyRepoDep,
    score_repo: ScoreRepoDep,
) -> RankingResponse:
    """Companies ranked by patent velocity."""
    return await _build_ranking(
        RankingMetric.PATENT_VELOCITY,
        company_repo,
        score_repo,
    )


@router.get("/stock-performance", response_model=RankingResponse)
async def get_stock_performance_rankings(
    company_repo: CompanyRepoDep,
    score_repo: ScoreRepoDep,
) -> RankingResponse:
    """Companies ranked by stock momentum."""
    return await _build_ranking(
        RankingMetric.STOCK_MOMENTUM,
        company_repo,
        score_repo,
    )


@router.get("/funding", response_model=RankingResponse)
async def get_funding_rankings(
    company_repo: CompanyRepoDep,
    score_repo: ScoreRepoDep,
) -> RankingResponse:
    """Companies ranked by funding strength."""
    return await _build_ranking(
        RankingMetric.FUNDING_STRENGTH,
        company_repo,
        score_repo,
    )


@router.get("/sentiment", response_model=RankingResponse)
async def get_sentiment_rankings(
    company_repo: CompanyRepoDep,
    score_repo: ScoreRepoDep,
) -> RankingResponse:
    """Companies ranked by news sentiment."""
    return await _build_ranking(
        RankingMetric.NEWS_SENTIMENT,
        company_repo,
        score_repo,
    )


@router.get("/government-contracts")
async def get_government_contract_rankings(
    company_repo: CompanyRepoDep,
    gov_contract_repo: GovContractRepoDep,
) -> dict:
    """Companies ranked by total government contract value."""
    companies = await company_repo.get_all()

    entries = []
    for company in companies:
        company_id = company.id or 0
        total_value = await gov_contract_repo.get_total_value(company_id)
        entries.append(
            {
                "rank": 0,
                "company": {
                    "id": company_id,
                    "name": company.name,
                    "slug": company.slug,
                    "sector": company.sector.value,
                    "ticker": company.ticker.symbol if company.ticker else None,
                    "description": company.description,
                    "is_etf": company.is_etf,
                    "website": company.website,
                    "logo_url": company.logo_url,
                },
                "metric_value": total_value,
                "trend": "flat",
            }
        )

    # Sort by contract value descending and assign ranks
    entries.sort(key=lambda e: e["metric_value"], reverse=True)
    for i, entry in enumerate(entries, 1):
        entry["rank"] = i

    return {
        "metric": "government_contracts",
        "entries": entries,
        "count": len(entries),
    }
