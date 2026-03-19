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
from src.infrastructure.sec_edgar_xbrl import SecEdgarXbrlAdapter
from src.infrastructure.sentiment import ClaudeSentimentAnalyzer
from src.infrastructure.usaspending_client import UsaSpendingAdapter
from src.infrastructure.uspto_client import UsptoPatentAdapter
from src.infrastructure.yahoo_finance import YahooFinanceAdapter
from src.usecases.calculate_score import ScoreInput, calculate_score
from src.usecases.rank_companies import rank_companies

if TYPE_CHECKING:
    from src.domain.models.entities import Company, NewsArticle

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

    prices = await stock_adapter.fetch_max_history(ticker)

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
    sector_str = company.sector.value if company.sector else None
    logger.info("Fetching news for %s (sector=%s)", company.name, sector_str)

    articles = await news_adapter.fetch_articles(
        company.name, ticker=ticker_str, limit=10, sector=sector_str
    )

    if not articles:
        logger.info("No news articles found for %s", company.name)
        return

    # Validate article URLs — skip broken links
    validated: list[NewsArticle] = []
    for article in articles:
        if await news_adapter.validate_url(article.url):
            validated.append(article)
        else:
            logger.warning(
                "Broken URL skipped for %s: %s", company.name, article.url
            )
    if len(validated) < len(articles):
        logger.info(
            "URL validation: kept %d/%d articles for %s",
            len(validated),
            len(articles),
            company.name,
        )
    articles = validated

    if not articles:
        logger.info("No valid news articles remaining for %s", company.name)
        return

    # Score sentiment if we have a Claude API key
    if not sentiment_analyzer._api_key:
        logger.warning(
            "No Claude API key — skipping sentiment for %s",
            company.name,
        )
    else:
        logger.info(
            "Analyzing sentiment for %d articles (%s)",
            len(articles),
            company.name,
        )
        scored_count = 0
        for article in articles:
            result = await sentiment_analyzer.analyze(article.title)
            if result is not None:
                label, confidence = result
                scored_count += 1
                logger.debug(
                    "Sentiment for '%s': %s (%.2f)",
                    article.title[:60],
                    label,
                    confidence,
                )
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
        logger.info(
            "Scored %d/%d articles for %s",
            scored_count,
            len(articles),
            company.name,
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

    # Fetch general filings (10-K, 10-Q)
    filings = await filing_adapter.fetch_filings(
        ticker, filing_types=["10-K", "10-Q"]
    )

    # Fetch Form 4 with enriched insider transaction details
    insider_filings = await filing_adapter.fetch_insider_trades(ticker)
    filings.extend(insider_filings)

    # Fetch 13F with enriched institution details
    inst_filings = await filing_adapter.fetch_institutional_holdings(
        ticker
    )
    filings.extend(inst_filings)

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
    from src.infrastructure.usaspending_client import ALTERNATE_SEARCH_NAMES

    logger.info(
        "Fetching government contracts for %s",
        company.name,
    )

    # Build search names: primary name + any known alternates
    search_names = [company.name]
    search_names.extend(ALTERNATE_SEARCH_NAMES.get(company.name, []))

    contracts = await usaspending_adapter.search_contracts_multi(search_names)
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
    "infleqtion": 12,
    "sealsq": 0,
    "btq-technologies": 0,
    "ibm": 1121,
    "alphabet-google": 105,
    "microsoft": 0,
    "amazon-aws": 0,
    "intel": 12,
    "honeywell-quantinuum": 56,
    "nvidia": 0,
    "fujitsu": 256,
    "defiance-quantum-etf": 0,
    "wisdomtree-quantum-etf": 0,
}

# Estimated quantum-computing patents filed in the last 12 months, derived from
# publicly available data (press releases, SEC filings, patent databases).
# Sources (as of early 2026):
#   IBM: 191 quantum patents granted in 2024 (GreyB, Benzinga)
#   Google: 168 quantum patents granted in 2024 (Benzinga)
#   Microsoft: ~546 total / 178 families; ~94 in last 5 yrs (GreyB)
#   D-Wave: 313 total patents, 210+ issued US patents (CB Insights, PatentVest)
#   IonQ: 1,060 total IP assets as of Aug 2025 (IonQ press release)
#   Rigetti: 252 issued+pending as of Aug 2025 (investor presentation)
#   Quantinuum: 410 publications / 188 families (PatentVest)
#   Arqit: ~52 registered patents (IPqwery/GreyB)
#   QUBT: 100+ patents from LSI acquisition + organic (SEC filings)
#   Zapata: 60+ patents granted+pending (GlobeNewswire Oct 2025)
#   Amazon/AWS: undisclosed, estimated from Ocelot + Braket activity
#   Intel: top-10 holder but second tier ~35/yr (QED-C, MIT QIR)
KNOWN_PATENT_COUNTS: dict[str, int] = {
    "ionq": 80,
    "d-wave-quantum": 40,
    "rigetti-computing": 45,
    "quantum-computing-inc": 15,
    "arqit-quantum": 12,
    "infleqtion": 25,
    "sealsq": 10,
    "btq-technologies": 5,
    "ibm": 190,
    "alphabet-google": 170,
    "microsoft": 50,
    "amazon-aws": 30,
    "intel": 35,
    "honeywell-quantinuum": 45,
    "nvidia": 40,
    "fujitsu": 60,
    "defiance-quantum-etf": 0,
    "wisdomtree-quantum-etf": 0,
}

async def recalculate_scores(
    companies: list[Company],
    stock_repo: PgStockRepository,
    patent_repo: PgPatentRepository,
    news_repo: PgNewsRepository,
    score_repo: PgScoreRepository,
    stock_adapter: YahooFinanceAdapter,
    gov_contract_repo: PgGovernmentContractRepository | None = None,
    xbrl_adapter: SecEdgarXbrlAdapter | None = None,
    sentiment_analyzer: ClaudeSentimentAnalyzer | None = None,
    filing_adapter: SecEdgarAdapter | None = None,
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
            if patent_count > 0:
                logger.info(
                    "Using known patent count %d for %s",
                    patent_count,
                    company.name,
                )

        # Qubit count: extract from recent news via Claude, fall back
        qubit_count = None
        if sentiment_analyzer and sentiment_analyzer._api_key:
            recent_articles = await news_repo.get_by_company(
                company_id, limit=20
            )
            titles = [a.title for a in recent_articles if a.title]
            if titles:
                qubit_count = await sentiment_analyzer.extract_qubit_count(
                    company.name, titles
                )
                if qubit_count is not None:
                    logger.info(
                        "Extracted qubit count %d for %s from news",
                        qubit_count,
                        company.name,
                    )
        if qubit_count is None:
            fallback = KNOWN_QUBIT_COUNTS.get(company.slug, 0)
            if fallback > 0:
                qubit_count = fallback
                logger.info(
                    "Using fallback qubit count %d for %s",
                    qubit_count,
                    company.name,
                )

        # Funding: combine SEC EDGAR XBRL (equity/assets) + Form D (private placements)
        total_funding = 0.0

        # Source 1: XBRL — stockholders' equity or total assets
        if xbrl_adapter and ticker:
            try:
                xbrl_funding = await xbrl_adapter.fetch_total_funding(ticker)
                if xbrl_funding is not None and xbrl_funding > 0:
                    total_funding = xbrl_funding
                    logger.info(
                        "SEC EDGAR XBRL funding for %s: $%.0f",
                        company.name,
                        total_funding,
                    )
            except Exception:
                logger.warning(
                    "XBRL funding fetch failed for %s",
                    company.name,
                )

        # Source 2: Form D — private placement / Reg D offering amounts
        if filing_adapter and ticker:
            try:
                form_d_amount = await filing_adapter.fetch_form_d_total_raised(
                    ticker
                )
                if form_d_amount is not None and form_d_amount > 0:
                    logger.info(
                        "SEC Form D total raised for %s: $%.0f",
                        company.name,
                        form_d_amount,
                    )
                    # Use the higher of XBRL equity vs Form D raised
                    total_funding = max(total_funding, form_d_amount)
            except Exception:
                logger.warning(
                    "Form D funding fetch failed for %s",
                    company.name,
                )

        if gov_contract_repo:
            gov_value = await gov_contract_repo.get_total_value(company_id)
            total_funding += gov_value

        # News sentiment average
        recent_news = await news_repo.get_by_company(company_id, limit=20)
        avg_sentiment = 0.0
        article_count = 0
        if recent_news:
            scored = [a for a in recent_news if a.sentiment_score is not None]
            if scored:
                article_count = len(scored)
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
        logger.info(
            "Score for %s: total=%.2f stock=%.2f patent=%.2f "
            "qubit=%.2f funding=%.2f news=%.2f "
            "(patents_filed=%s, qubits=%s, funding=$%s)",
            company.name,
            score.total_score,
            score.stock_momentum,
            score.patent_velocity,
            score.qubit_progress,
            score.funding_strength,
            score.news_sentiment,
            patent_count,
            qubit_count,
            total_funding,
        )
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
    xbrl_adapter = SecEdgarXbrlAdapter(
        user_agent=settings.sec_edgar_user_agent,
    )

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
                xbrl_adapter,
                sentiment_analyzer,
                filing_adapter,
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
