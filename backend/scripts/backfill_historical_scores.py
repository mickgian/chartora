"""Backfill historical Quantum Power Scores from real data.

Computes scores for each company for each trading day over the past ~400 days
using data already in the database (stock prices) plus curated public data
(qubit milestones, known patent counts, funding carry-back).

News sentiment defaults to neutral (score=50) for backfilled dates since
free historical sentiment data is not available.

Usage:
    python -m scripts.backfill_historical_scores
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.infrastructure.database import (
    CompanyTable,
    GovernmentContractTable,
    ScoreTable,
    StockPriceTable,
)
from src.usecases.calculate_score import ScoreInput, calculate_score
from src.usecases.rank_companies import rank_companies

if TYPE_CHECKING:
    from src.domain.models.entities import QuantumPowerScore

# Load .env from backend/ directory
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# ---------------------------------------------------------------------------
# Curated qubit milestone timelines from public press releases / announcements
# Each entry: (effective_date, qubit_count)
# Sorted ascending by date.  For any date T the script uses the most recent
# milestone at or before T.
# ---------------------------------------------------------------------------
QUBIT_MILESTONES: dict[str, list[tuple[date, int]]] = {
    "ibm": [
        (date(2021, 11, 16), 127),    # Eagle 127-qubit processor
        (date(2022, 11, 9), 433),      # Osprey 433-qubit processor
        (date(2023, 12, 4), 1121),     # Condor 1121-qubit processor
    ],
    "alphabet-google": [
        (date(2019, 10, 23), 53),      # Sycamore 53-qubit
        (date(2024, 12, 9), 105),      # Willow 105-qubit processor
    ],
    "d-wave-quantum": [
        (date(2020, 9, 29), 5000),     # Advantage 5000+ qubit
    ],
    "ionq": [
        (date(2023, 10, 3), 29),       # Forte #AQ 29
        (date(2024, 9, 10), 36),       # Forte Enterprise #AQ 36
    ],
    "rigetti-computing": [
        (date(2022, 6, 29), 80),       # Aspen-M-3 80 qubits
        (date(2024, 1, 8), 84),        # Ankaa-2 84-qubit processor
    ],
    "honeywell-quantinuum": [
        (date(2023, 5, 9), 32),        # H1-1 upgrade 32 qubits
        (date(2024, 3, 14), 56),       # H2 56-qubit processor
    ],
    "intel": [
        (date(2023, 6, 15), 12),       # Tunnel Falls 12-qubit silicon
    ],
    "infleqtion": [
        (date(2024, 6, 1), 12),        # Sqorpius neutral-atom processor
    ],
    "fujitsu": [
        (date(2023, 10, 5), 64),       # Superconducting 64-qubit with RIKEN
        (date(2025, 3, 1), 256),       # 256-qubit system announced
    ],
    "nvidia": [],                       # GPU/software platform, no own qubits
    # Companies with 0 qubits (no quantum hardware)
    "quantum-computing-inc": [],
    "arqit-quantum": [],
    "sealsq": [],
    "btq-technologies": [],
    "quantumctek": [],
    "quantum-emotion": [],
    "01-communique": [],
    "microsoft": [],
    "amazon-aws": [],
    "defiance-quantum-etf": [],
    "wisdomtree-quantum-etf": [],
    "vaneck-quantum-etf": [],
    "ishares-quantum-etf": [],
    "globalx-ai-quantum-etf": [],
}

# Known annual patent filing counts — same as in refresh_data.py.
# Treated as constant over the 1-year backfill window.
KNOWN_PATENT_COUNTS: dict[str, int] = {
    "ionq": 80,
    "d-wave-quantum": 40,
    "rigetti-computing": 45,
    "quantum-computing-inc": 15,
    "arqit-quantum": 12,
    "infleqtion": 25,
    "sealsq": 10,
    "btq-technologies": 5,
    "quantumctek": 20,
    "quantum-emotion": 5,
    "01-communique": 8,
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
    "vaneck-quantum-etf": 0,
    "ishares-quantum-etf": 0,
    "globalx-ai-quantum-etf": 0,
}


def _get_qubit_count_at_date(slug: str, target: date) -> int | None:
    """Look up the qubit count for a company at a given date."""
    milestones = QUBIT_MILESTONES.get(slug, [])
    if not milestones:
        return 0
    # Find the latest milestone at or before the target date
    best = None
    for milestone_date, count in milestones:
        if milestone_date <= target:
            best = count
    return best


def _compute_stock_return(
    prices: dict[date, float],
    target: date,
    days: int,
) -> float | None:
    """Compute stock return over N days ending at target date.

    Finds the closest available trading day to both target and target-days.
    Returns percentage change, or None if data is insufficient.
    """
    # Find closest trading day at or before target
    end_price = None
    for offset in range(5):  # look back up to 5 days for trading day
        d = target - timedelta(days=offset)
        if d in prices:
            end_price = prices[d]
            break
    if end_price is None:
        return None

    # Find closest trading day at or before (target - days)
    start_target = target - timedelta(days=days)
    start_price = None
    for offset in range(10):  # wider search for start
        d = start_target - timedelta(days=offset)
        if d in prices:
            start_price = prices[d]
            break
    if start_price is None or start_price == 0:
        return None

    return round((end_price - start_price) / start_price * 100, 2)


async def backfill(
    start_date: date | None = None,
    end_date: date | None = None,
) -> None:
    """Run the historical score backfill."""
    database_url = os.environ.get(
        "CHARTORA_DATABASE_URL",
        "postgresql+asyncpg://chartora:chartora@localhost:5432/chartora",
    )
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    if end_date is None:
        end_date = date(2026, 3, 15)  # Day before live data started
    if start_date is None:
        start_date = end_date - timedelta(days=400)

    logger.info(
        "Backfilling scores from %s to %s", start_date, end_date
    )

    async with session_factory() as session:
        # Load all companies
        result = await session.execute(select(CompanyTable))
        company_rows = result.scalars().all()
        companies = {
            row.slug: {"id": row.id, "ticker": row.ticker, "slug": row.slug}
            for row in company_rows
        }
        logger.info("Loaded %d companies", len(companies))

        # Load stock prices for all companies in the needed date range
        # We need prices from (start_date - 90 days) to end_date for return calculations
        price_start = start_date - timedelta(days=100)
        stock_result = await session.execute(
            select(StockPriceTable).where(
                StockPriceTable.price_date >= price_start,
                StockPriceTable.price_date <= end_date,
            )
        )
        stock_rows = stock_result.scalars().all()

        # Build price lookup: company_id -> {date -> close_price}
        price_map: dict[int, dict[date, float]] = {}
        for row in stock_rows:
            if row.company_id not in price_map:
                price_map[row.company_id] = {}
            price_map[row.company_id][row.price_date] = float(row.close_price)
        logger.info(
            "Loaded stock prices for %d companies", len(price_map)
        )

        # Load total government contract values per company
        gov_result = await session.execute(
            select(
                GovernmentContractTable.company_id,
                func.coalesce(func.sum(GovernmentContractTable.amount), 0).label(
                    "total"
                ),
            ).group_by(GovernmentContractTable.company_id)
        )
        gov_totals: dict[int, float] = {
            row.company_id: float(row.total) for row in gov_result
        }

        # Load XBRL/funding data from the most recent live scores (March 16+)
        # to carry back. The funding_strength normalized value gives us a
        # reference, but we need the raw funding input.  Since we don't store
        # raw inputs, we'll use gov contract totals as a reasonable proxy.
        # For big-tech companies, their market cap dwarfs quantum-specific
        # funding, so we use gov contracts as the primary funding signal
        # for backfill (same data that's in the DB).

        # Collect all trading dates in range
        all_dates: set[date] = set()
        for prices in price_map.values():
            for d in prices:
                if start_date <= d <= end_date:
                    all_dates.add(d)
        trading_dates = sorted(all_dates)
        logger.info(
            "Found %d unique trading dates to backfill", len(trading_dates)
        )

        if not trading_dates:
            logger.warning("No trading dates found — is stock data loaded?")
            await engine.dispose()
            return

        # Process each date
        prev_day_scores: list[QuantumPowerScore] = []
        batch_size = 20  # save in batches of 20 days
        pending_scores: list[QuantumPowerScore] = []

        for date_idx, score_date in enumerate(trading_dates):
            day_scores = []

            for slug, company in companies.items():
                company_id = company["id"]
                prices = price_map.get(company_id, {})

                # Stock momentum
                r30 = _compute_stock_return(prices, score_date, 30)
                r60 = _compute_stock_return(prices, score_date, 60)
                r90 = _compute_stock_return(prices, score_date, 90)

                # Patent velocity — use known annual counts
                patent_count = KNOWN_PATENT_COUNTS.get(slug, 0)

                # Qubit progress — use milestone timeline
                qubit_count = _get_qubit_count_at_date(slug, score_date)

                # Funding — use gov contract totals from DB
                total_funding = gov_totals.get(company_id, 0.0)

                # News sentiment — neutral (no historical data)
                avg_sentiment = 0.0
                article_count = 0

                score_input = ScoreInput(
                    company_id=company_id,
                    score_date=score_date,
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
                day_scores.append(score)

            # Rank companies for this date
            result = rank_companies(day_scores, previous_scores=prev_day_scores)
            for rc in result.rankings:
                for s in day_scores:
                    if s.company_id == rc.company_id:
                        object.__setattr__(s, "rank", rc.rank)
                        object.__setattr__(s, "rank_change", rc.rank_change)
                        break

            pending_scores.extend(day_scores)
            prev_day_scores = day_scores

            # Save in batches
            if len(pending_scores) >= batch_size * len(companies) or (
                date_idx == len(trading_dates) - 1
            ):
                await _save_scores_batch(session, pending_scores)
                logger.info(
                    "Saved scores through %s (%d/%d dates)",
                    score_date,
                    date_idx + 1,
                    len(trading_dates),
                )
                pending_scores = []

        await session.commit()
        logger.info("Backfill complete.")

    await engine.dispose()


async def _save_scores_batch(
    session: async_sessionmaker,
    scores: list[QuantumPowerScore],
) -> None:
    """Save a batch of scores using upsert."""
    if not scores:
        return

    from sqlalchemy.dialects.postgresql import insert as pg_insert

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
    await session.execute(stmt)
    await session.flush()


def main() -> None:
    """Entry point."""
    start = None
    end = None
    for arg in sys.argv[1:]:
        if arg.startswith("--start="):
            start = date.fromisoformat(arg.split("=", 1)[1])
        elif arg.startswith("--end="):
            end = date.fromisoformat(arg.split("=", 1)[1])
    asyncio.run(backfill(start_date=start, end_date=end))


if __name__ == "__main__":
    main()
