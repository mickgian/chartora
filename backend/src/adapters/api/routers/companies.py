"""Company detail API endpoints."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Query

from src.adapters.api.dependencies import (  # noqa: TC001
    CompanyRepoDep,
    FilingRepoDep,
    NewsRepoDep,
    PatentRepoDep,
    ScoreRepoDep,
    StockDataSourceDep,
    StockRepoDep,
)
from src.adapters.api.schemas import (
    CompanyDetailResponse,
    CompanyResponse,
    FilingListResponse,
    FilingResponse,
    IntradayPriceResponse,
    IntradayResponse,
    NewsArticleResponse,
    NewsListResponse,
    PatentListResponse,
    PatentResponse,
    ScoreResponse,
    StockHistoryResponse,
    StockPriceResponse,
)
from src.domain.models.value_objects import DateRange

if TYPE_CHECKING:
    from src.domain.models.entities import Company

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


def _company_to_response(company: Company) -> CompanyResponse:
    return CompanyResponse(
        id=company.id or 0,
        name=company.name,
        slug=company.slug,
        sector=company.sector.value,
        ticker=(company.ticker.symbol if company.ticker else None),
        description=company.description,
        is_etf=company.is_etf,
        website=company.website,
        logo_url=company.logo_url,
    )


@router.get("/{slug}", response_model=CompanyDetailResponse)
async def get_company(
    slug: str,
    company_repo: CompanyRepoDep,
    score_repo: ScoreRepoDep,
) -> CompanyDetailResponse:
    """Get full company profile."""
    logger.info("[COMPANY] Fetching company slug=%s", slug)
    company = await company_repo.get_by_slug(slug)
    if company is None:
        logger.warning("[COMPANY] Company not found slug=%s", slug)
        raise HTTPException(
            status_code=404,
            detail=f"Company '{slug}' not found",
        )

    score = await score_repo.get_latest(company.id or 0)
    score_resp = None
    if score is not None:
        score_resp = ScoreResponse(
            total_score=score.total_score,
            stock_momentum=score.stock_momentum,
            patent_velocity=score.patent_velocity,
            qubit_progress=score.qubit_progress,
            funding_strength=score.funding_strength,
            news_sentiment=score.news_sentiment,
            score_date=score.score_date,
            rank=score.rank,
            rank_change=score.rank_change,
        )

    logger.info(
        "[COMPANY] slug=%s company_id=%s has_score=%s",
        slug,
        company.id,
        score_resp is not None,
    )
    return CompanyDetailResponse(
        company=_company_to_response(company),
        score=score_resp,
    )


@router.get("/{slug}/stock", response_model=StockHistoryResponse)
async def get_company_stock(
    slug: str,
    company_repo: CompanyRepoDep,
    stock_repo: StockRepoDep,
    days: int | None = Query(
        default=None,
        ge=1,
        le=7300,
        description="Number of days of history. Omit to retrieve all available data.",
    ),
) -> StockHistoryResponse:
    """Get stock price history for a company."""
    logger.info("[STOCK] Fetching stock history slug=%s days=%s", slug, days)
    company = await company_repo.get_by_slug(slug)
    if company is None:
        logger.warning("[STOCK] Company not found slug=%s", slug)
        raise HTTPException(
            status_code=404,
            detail=f"Company '{slug}' not found",
        )

    company_id = company.id or 0

    if days is None:
        logger.info("[STOCK] Querying ALL prices for company_id=%d", company_id)
        prices = await stock_repo.get_all_for_company(company_id)
    else:
        end = date.today()
        start = end - timedelta(days=days)
        date_range = DateRange(start=start, end=end)
        logger.info(
            "[STOCK] Querying company_id=%d date_range=%s to %s",
            company_id,
            start,
            end,
        )
        prices = await stock_repo.get_by_date_range(company_id, date_range)

    logger.info(
        "[STOCK] slug=%s company_id=%d returned %d prices",
        slug,
        company_id,
        len(prices),
    )
    if prices:
        logger.info(
            "[STOCK] First price: %s, Last price: %s",
            prices[0].price_date,
            prices[-1].price_date,
        )

    return StockHistoryResponse(
        company_slug=slug,
        prices=[
            StockPriceResponse(
                price_date=p.price_date,
                close_price=float(p.close_price),
                open_price=(float(p.open_price) if p.open_price is not None else None),
                high_price=(float(p.high_price) if p.high_price is not None else None),
                low_price=(float(p.low_price) if p.low_price is not None else None),
                volume=p.volume,
                market_cap=p.market_cap,
            )
            for p in prices
        ],
        count=len(prices),
    )


@router.get("/{slug}/stock/intraday", response_model=IntradayResponse)
async def get_company_intraday(
    slug: str,
    company_repo: CompanyRepoDep,
    stock_source: StockDataSourceDep,
) -> IntradayResponse:
    """Get intraday (hourly) stock prices for a company."""
    logger.info("[INTRADAY] Fetching intraday data slug=%s", slug)
    company = await company_repo.get_by_slug(slug)
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company '{slug}' not found")

    if company.ticker is None:
        return IntradayResponse(company_slug=slug, prices=[], count=0)

    prices = await stock_source.fetch_intraday(company.ticker.symbol)
    logger.info("[INTRADAY] slug=%s returned %d intraday prices", slug, len(prices))

    return IntradayResponse(
        company_slug=slug,
        prices=[
            IntradayPriceResponse(
                timestamp=p.timestamp,
                price=float(p.price),
                volume=p.volume,
            )
            for p in prices
        ],
        count=len(prices),
    )


@router.get("/{slug}/patents", response_model=PatentListResponse)
async def get_company_patents(
    slug: str,
    company_repo: CompanyRepoDep,
    patent_repo: PatentRepoDep,
) -> PatentListResponse:
    """Get patent timeline for a company."""
    logger.info("[PATENTS] Fetching patents for slug=%s", slug)
    company = await company_repo.get_by_slug(slug)
    if company is None:
        logger.warning("[PATENTS] Company not found slug=%s", slug)
        raise HTTPException(
            status_code=404,
            detail=f"Company '{slug}' not found",
        )

    patents = await patent_repo.get_by_company(company.id or 0)
    logger.info("[PATENTS] slug=%s returned %d patents", slug, len(patents))

    return PatentListResponse(
        company_slug=slug,
        patents=[
            PatentResponse(
                patent_number=p.patent_number,
                title=p.title,
                filing_date=p.filing_date,
                source=p.source.value,
                abstract=p.abstract,
                grant_date=p.grant_date,
                classification=p.classification,
            )
            for p in patents
        ],
        count=len(patents),
    )


@router.get("/{slug}/news", response_model=NewsListResponse)
async def get_company_news(
    slug: str,
    company_repo: CompanyRepoDep,
    news_repo: NewsRepoDep,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of articles",
    ),
) -> NewsListResponse:
    """Get recent news with sentiment for a company."""
    logger.info("[NEWS] Fetching news for slug=%s limit=%d", slug, limit)
    company = await company_repo.get_by_slug(slug)
    if company is None:
        logger.warning("[NEWS] Company not found slug=%s", slug)
        raise HTTPException(
            status_code=404,
            detail=f"Company '{slug}' not found",
        )

    articles = await news_repo.get_by_company(company.id or 0, limit=limit)
    logger.info("[NEWS] slug=%s returned %d articles", slug, len(articles))

    return NewsListResponse(
        company_slug=slug,
        articles=[
            NewsArticleResponse(
                title=a.title,
                url=a.url,
                published_at=a.published_at,
                source_name=a.source_name,
                sentiment=(a.sentiment.value if a.sentiment else None),
                sentiment_score=(
                    float(a.sentiment_score) if a.sentiment_score is not None else None
                ),
            )
            for a in articles
        ],
        count=len(articles),
    )


@router.get("/{slug}/filings", response_model=FilingListResponse)
async def get_company_filings(
    slug: str,
    company_repo: CompanyRepoDep,
    filing_repo: FilingRepoDep,
) -> FilingListResponse:
    """Get SEC filings summary for a company."""
    logger.info("[FILINGS] Fetching filings for slug=%s", slug)
    company = await company_repo.get_by_slug(slug)
    if company is None:
        logger.warning("[FILINGS] Company not found slug=%s", slug)
        raise HTTPException(
            status_code=404,
            detail=f"Company '{slug}' not found",
        )

    filings = await filing_repo.get_by_company(company.id or 0)
    logger.info("[FILINGS] slug=%s returned %d filings", slug, len(filings))

    return FilingListResponse(
        company_slug=slug,
        filings=[
            FilingResponse(
                filing_type=f.filing_type.value,
                filing_date=f.filing_date,
                description=f.description,
                url=f.url,
            )
            for f in filings
        ],
        count=len(filings),
    )
