"""Data refresh orchestrator — cron-compatible script.

Pulls fresh data from all external sources, recalculates scores,
and stores everything in PostgreSQL. Idempotent and safe to re-run.

Usage:
    python -m scripts.refresh_data
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from src.adapters.repositories import (
    PgCompanyRepository,
    PgFilingRepository,
    PgGovernmentContractRepository,
    PgNewsRepository,
    PgPatentRepository,
    PgScoreRepository,
    PgStockRepository,
)
from src.config.settings import Settings
from src.domain.models.value_objects import DateRange, SentimentLabel
from src.infrastructure.news_client import NewsApiAdapter
from src.infrastructure.sec_edgar import SecEdgarAdapter
from src.infrastructure.sentiment import ClaudeSentimentAnalyzer
from src.infrastructure.usaspending_client import UsaSpendingAdapter
from src.infrastructure.uspto_client import UsptoPatentAdapter
from src.infrastructure.yahoo_finance import YahooFinanceAdapter
from src.usecases.calculate_score import ScoreInput, calculate_score
from src.usecases.rank_companies import rank_companies

if TYPE_CHECKING:
    from src.domain.models.entities import Company

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def refresh_stock_data(
    company: Company,
    stock_adapter: YahooFinanceAdapter,
    stock_repo: PgStockRepository,
) -> None:
    """Pull fresh stock data for a single company."""
    if company.ticker is None:
        logger.info(
            "Skipping stock data for %s (no ticker)",
            company.name,
        )
        return

    ticker = company.ticker.symbol
    logger.info(
        "Fetching stock data for %s (%s)",
        company.name,
        ticker,
    )

    today = date.today()
    date_range = DateRange(start=today - timedelta(days=7), end=today)
    prices = await stock_adapter.fetch_history(ticker, date_range)

    if not prices:
        logger.warning("No stock data returned for %s", ticker)
        return

    # Set company_id on all prices
    for p in prices:
        object.__setattr__(p, "company_id", company.id)

    await stock_repo.save_many(prices)
    logger.info(
        "Saved %d stock prices for %s",
        len(prices),
        company.name,
    )


async def refresh_patent_data(
    company: Company,
    patent_adapter: UsptoPatentAdapter,
    patent_repo: PgPatentRepository,
) -> None:
    """Pull new patent filings for a single company."""
    logger.info("Fetching patent data for %s", company.name)

    today = date.today()
    date_range = DateRange(start=today - timedelta(days=30), end=today)
    patents = await patent_adapter.search_patents(company.name, date_range)

    if not patents:
        logger.info("No new patents found for %s", company.name)
        return

    for p in patents:
        object.__setattr__(p, "company_id", company.id)

    await patent_repo.save_many(patents)
    logger.info(
        "Saved %d patents for %s",
        len(patents),
        company.name,
    )


async def refresh_news_data(
    company: Company,
    news_adapter: NewsApiAdapter,
    sentiment_analyzer: ClaudeSentimentAnalyzer,
    news_repo: PgNewsRepository,
) -> None:
    """Pull news headlines and score sentiment."""
    if not news_adapter._api_key:
        logger.info(
            "Skipping news for %s (no API key)",
            company.name,
        )
        return

    ticker_str = company.ticker.symbol if company.ticker else None
    logger.info("Fetching news for %s", company.name)

    articles = await news_adapter.fetch_articles(
        company.name, ticker=ticker_str, limit=10
    )

    if not articles:
        logger.info("No news articles found for %s", company.name)
        return

    # Score sentiment if we have a Claude API key
    if sentiment_analyzer._api_key:
        logger.info(
            "Analyzing sentiment for %d articles (%s)",
            len(articles),
            company.name,
        )
        for article in articles:
            label, confidence = await sentiment_analyzer.analyze(article.title)
            object.__setattr__(
                article,
                "sentiment",
                SentimentLabel(label),
            )
            object.__setattr__(
                article,
                "sentiment_score",
                Decimal(str(round(confidence, 2))),
            )

    for a in articles:
        object.__setattr__(a, "company_id", company.id)

    await news_repo.save_many(articles)
    logger.info(
        "Saved %d news articles for %s",
        len(articles),
        company.name,
    )


async def refresh_filing_data(
    company: Company,
    filing_adapter: SecEdgarAdapter,
    filing_repo: PgFilingRepository,
) -> None:
    """Pull SEC filings for a single company."""
    if company.ticker is None:
        logger.info(
            "Skipping filings for %s (no ticker)",
            company.name,
        )
        return

    ticker = company.ticker.symbol
    logger.info("Fetching SEC filings for %s (%s)", company.name, ticker)

    filings = await filing_adapter.fetch_filings(ticker)
    if not filings:
        logger.info("No filings returned for %s", ticker)
        return

    for f in filings:
        object.__setattr__(f, "company_id", company.id)

    await filing_repo.save_many(filings)
    logger.info(
        "Saved %d filings for %s",
        len(filings),
        company.name,
    )


async def refresh_government_contracts(
    company: Company,
    usaspending_adapter: UsaSpendingAdapter,
    gov_contract_repo: PgGovernmentContractRepository,
) -> None:
    """Pull government contracts for a single company."""
    logger.info(
        "Fetching government contracts for %s",
        company.name,
    )

    contracts = await usaspending_adapter.search_contracts(company.name)
    if not contracts:
        logger.info("No government contracts found for %s", company.name)
        return

    for c in contracts:
        object.__setattr__(c, "company_id", company.id)

    await gov_contract_repo.save_many(contracts)
    logger.info(
        "Saved %d government contracts for %s",
        len(contracts),
        company.name,
    )


KNOWN_QUBIT_COUNTS: dict[str, int] = {
    "ionq": 36,
    "d-wave-quantum": 5000,
    "rigetti-computing": 84,
    "quantum-computing-inc": 0,
    "arqit-quantum": 0,
    "zapata-computing": 0,
    "ibm": 1121,
    "alphabet-google": 105,
    "microsoft": 0,
    "amazon-aws": 0,
    "intel": 12,
    "honeywell-quantinuum": 56,
    "defiance-quantum-etf": 0,
    "ark-space-exploration-etf": 0,
}

KNOWN_PATENT_COUNTS: dict[str, int] = {
    "ionq": 25,
    "d-wave-quantum": 15,
    "rigetti-computing": 12,
    "quantum-computing-inc": 3,
    "arqit-quantum": 8,
    "zapata-computing": 5,
    "ibm": 150,
    "alphabet-google": 80,
    "microsoft": 45,
    "amazon-aws": 20,
    "intel": 30,
    "honeywell-quantinuum": 35,
    "defiance-quantum-etf": 0,
    "ark-space-exploration-etf": 0,
}

KNOWN_FUNDING_USD: dict[str, float] = {
    "ionq": 634_000_000.0,
    "d-wave-quantum": 340_000_000.0,
    "rigetti-computing": 294_000_000.0,
    "quantum-computing-inc": 70_000_000.0,
    "arqit-quantum": 100_000_000.0,
    "zapata-computing": 64_000_000.0,
    "ibm": 0.0,
    "alphabet-google": 0.0,
    "microsoft": 0.0,
    "amazon-aws": 0.0,
    "intel": 0.0,
    "honeywell-quantinuum": 300_000_000.0,
    "defiance-quantum-etf": 0.0,
    "ark-space-exploration-etf": 0.0,
}


async def recalculate_scores(
    companies: list[Company],
    stock_repo: PgStockRepository,
    patent_repo: PgPatentRepository,
    news_repo: PgNewsRepository,
    score_repo: PgScoreRepository,
    stock_adapter: YahooFinanceAdapter,
    gov_contract_repo: PgGovernmentContractRepository | None = None,
) -> None:
    """Recalculate Quantum Power Scores for all companies."""
    logger.info(
        "Recalculating scores for %d companies",
        len(companies),
    )
    today = date.today()
    twelve_months_ago = DateRange(start=today - timedelta(days=365), end=today)

    scores = []
    for company in companies:
        company_id = company.id or 0
        ticker = company.ticker.symbol if company.ticker else None

        # Stock performance
        r30 = r60 = r90 = None
        if ticker:
            r30 = await stock_adapter.fetch_performance(ticker, 30)
            r60 = await stock_adapter.fetch_performance(ticker, 60)
            r90 = await stock_adapter.fetch_performance(ticker, 90)

        # Patent count (last 12 months) — fall back to known data if API unavailable
        patent_count = await patent_repo.count_by_date_range(
            company_id, twelve_months_ago
        )
        if patent_count == 0:
            patent_count = KNOWN_PATENT_COUNTS.get(company.slug, 0)

        # Qubit count from known data
        qubit_count = KNOWN_QUBIT_COUNTS.get(company.slug, 0) or None

        # Funding: use known seed funding + government contract values
        total_funding = KNOWN_FUNDING_USD.get(company.slug, 0.0)
        if gov_contract_repo:
            gov_value = await gov_contract_repo.get_total_value(company_id)
            total_funding += gov_value

        # News sentiment average
        recent_news = await news_repo.get_by_company(company_id, limit=20)
        avg_sentiment = 0.0
        article_count = len(recent_news)
        if recent_news:
            scored = [a for a in recent_news if a.sentiment_score is not None]
            if scored:
                sentiment_values = []
                for a in scored:
                    label = a.sentiment
                    conf = float(a.sentiment_score or 0)
                    if label and label.value == "bullish":
                        sentiment_values.append(conf)
                    elif label and label.value == "bearish":
                        sentiment_values.append(-conf)
                    else:
                        sentiment_values.append(0.0)
                avg_sentiment = sum(sentiment_values) / len(sentiment_values)

        score_input = ScoreInput(
            company_id=company_id,
            score_date=today,
            stock_return_30d=r30,
            stock_return_60d=r60,
            stock_return_90d=r90,
            patents_filed_12m=patent_count,
            qubit_count=qubit_count,
            total_funding_usd=total_funding if total_funding > 0 else None,
            avg_sentiment=avg_sentiment,
            article_count=article_count,
        )
        score = calculate_score(score_input)
        scores.append(score)

    # Rank and assign ranks
    if scores:
        result = rank_companies(scores)
        for rc in result.rankings:
            for s in scores:
                if s.company_id == rc.company_id:
                    object.__setattr__(s, "rank", rc.rank)
                    object.__setattr__(
                        s,
                        "rank_change",
                        rc.rank_change,
                    )
                    break

        await score_repo.save_many(scores)
        logger.info("Saved scores for %d companies", len(scores))


async def run_refresh(
    settings: Settings | None = None,
) -> None:
    """Run the full data refresh pipeline."""
    if settings is None:
        settings = Settings()

    logger.info("Starting data refresh pipeline")

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Initialize adapters
    stock_adapter = YahooFinanceAdapter()
    patent_adapter = UsptoPatentAdapter(api_key=settings.uspto_api_key or None)
    news_adapter = NewsApiAdapter(api_key=settings.news_api_key)
    sentiment_analyzer = ClaudeSentimentAnalyzer(api_key=settings.claude_api_key)
    filing_adapter = SecEdgarAdapter()
    usaspending_adapter = UsaSpendingAdapter()

    async with session_factory() as session:
        # Initialize repositories
        company_repo = PgCompanyRepository(session)
        stock_repo = PgStockRepository(session)
        patent_repo = PgPatentRepository(session)
        news_repo = PgNewsRepository(session)
        score_repo = PgScoreRepository(session)
        filing_repo = PgFilingRepository(session)
        gov_contract_repo = PgGovernmentContractRepository(session)

        # Get all companies
        companies = await company_repo.get_all()
        if not companies:
            logger.warning("No companies found in database. Run seed script first.")
            return

        logger.info("Processing %d companies", len(companies))

        # Step 1: Refresh stock data
        for company in companies:
            try:
                await refresh_stock_data(company, stock_adapter, stock_repo)
            except Exception:
                logger.exception(
                    "Error refreshing stock data for %s",
                    company.name,
                )
                await session.rollback()

        # Step 2: Refresh patent data
        for company in companies:
            try:
                await refresh_patent_data(company, patent_adapter, patent_repo)
            except Exception:
                logger.exception(
                    "Error refreshing patent data for %s",
                    company.name,
                )
                await session.rollback()

        # Step 3: Refresh news + sentiment
        for company in companies:
            try:
                await refresh_news_data(
                    company,
                    news_adapter,
                    sentiment_analyzer,
                    news_repo,
                )
            except Exception:
                logger.exception(
                    "Error refreshing news for %s",
                    company.name,
                )
                await session.rollback()

        # Step 4: Refresh SEC filings
        for company in companies:
            try:
                await refresh_filing_data(
                    company, filing_adapter, filing_repo
                )
            except Exception:
                logger.exception(
                    "Error refreshing filings for %s",
                    company.name,
                )
                await session.rollback()

        # Step 5: Refresh government contracts
        for company in companies:
            try:
                await refresh_government_contracts(
                    company, usaspending_adapter, gov_contract_repo
                )
            except Exception:
                logger.exception(
                    "Error refreshing gov contracts for %s",
                    company.name,
                )
                await session.rollback()

        # Step 6: Recalculate scores
        try:
            await recalculate_scores(
                companies,
                stock_repo,
                patent_repo,
                news_repo,
                score_repo,
                stock_adapter,
                gov_contract_repo,
            )
        except Exception:
            logger.exception("Error recalculating scores")
            await session.rollback()

        await session.commit()

    await engine.dispose()
    logger.info("Data refresh pipeline complete")


def main() -> None:
    """Entry point for the refresh script."""
    asyncio.run(run_refresh())


if __name__ == "__main__":
    main()
