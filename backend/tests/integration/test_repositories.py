"""Integration tests for PostgreSQL repository implementations.

Uses SQLite in-memory database for testing since the repository
implementations use SQLAlchemy ORM which is database-agnostic.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.adapters.repositories import (
    PgCompanyRepository,
    PgFilingRepository,
    PgNewsRepository,
    PgPatentRepository,
    PgScoreRepository,
    PgStockRepository,
)
from src.domain.models.entities import (
    Company,
    Filing,
    NewsArticle,
    Patent,
    QuantumPowerScore,
    StockPrice,
)
from src.domain.models.value_objects import (
    DateRange,
    FilingType,
    PatentSource,
    Sector,
    SentimentLabel,
    Ticker,
)
from src.infrastructure.database import Base


@pytest.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    # Enable foreign keys for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(engine):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


# ─── Company Repository ──────────────────────────────────────────────────────


class TestPgCompanyRepository:
    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, session):
        repo = PgCompanyRepository(session)
        company = Company(
            name="IonQ",
            slug="ionq",
            sector=Sector.PURE_PLAY,
            ticker=Ticker("IONQ"),
            description="Quantum computing company",
        )

        saved = await repo.save(company)
        assert saved.id is not None

        retrieved = await repo.get_by_id(saved.id)
        assert retrieved is not None
        assert retrieved.name == "IonQ"
        assert retrieved.slug == "ionq"
        assert retrieved.ticker.symbol == "IONQ"
        assert retrieved.sector == Sector.PURE_PLAY

    @pytest.mark.asyncio
    async def test_get_by_slug(self, session):
        repo = PgCompanyRepository(session)
        company = Company(name="D-Wave", slug="d-wave", sector=Sector.PURE_PLAY)
        await repo.save(company)

        retrieved = await repo.get_by_slug("d-wave")
        assert retrieved is not None
        assert retrieved.name == "D-Wave"

    @pytest.mark.asyncio
    async def test_get_by_slug_not_found(self, session):
        repo = PgCompanyRepository(session)
        result = await repo.get_by_slug("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, session):
        repo = PgCompanyRepository(session)
        await repo.save(Company(name="Alpha", slug="alpha", sector=Sector.PURE_PLAY))
        await repo.save(Company(name="Beta", slug="beta", sector=Sector.BIG_TECH))

        companies = await repo.get_all()
        assert len(companies) == 2
        # Ordered by name
        assert companies[0].name == "Alpha"
        assert companies[1].name == "Beta"

    @pytest.mark.asyncio
    async def test_update_existing(self, session):
        repo = PgCompanyRepository(session)
        company = Company(name="IonQ", slug="ionq", sector=Sector.PURE_PLAY)
        saved = await repo.save(company)

        saved.description = "Updated description"
        updated = await repo.save(saved)
        assert updated.description == "Updated description"

    @pytest.mark.asyncio
    async def test_delete(self, session):
        repo = PgCompanyRepository(session)
        company = Company(name="ToDelete", slug="to-delete", sector=Sector.PURE_PLAY)
        saved = await repo.save(company)

        await repo.delete(saved.id)
        result = await repo.get_by_id(saved.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_company_without_ticker(self, session):
        repo = PgCompanyRepository(session)
        company = Company(
            name="Quantum Startup",
            slug="quantum-startup",
            sector=Sector.PURE_PLAY,
            ticker=None,
        )
        saved = await repo.save(company)
        retrieved = await repo.get_by_id(saved.id)
        assert retrieved.ticker is None


# ─── Stock Repository ─────────────────────────────────────────────────────────


class TestPgStockRepository:
    @pytest.fixture
    async def company_id(self, session):
        repo = PgCompanyRepository(session)
        company = await repo.save(
            Company(name="IonQ", slug="ionq", sector=Sector.PURE_PLAY)
        )
        return company.id

    @pytest.mark.asyncio
    async def test_save_and_get_latest(self, session, company_id):
        repo = PgStockRepository(session)
        sp = StockPrice(
            company_id=company_id,
            price_date=date(2025, 6, 15),
            close_price=Decimal("25.50"),
            open_price=Decimal("25.00"),
            high_price=Decimal("26.00"),
            low_price=Decimal("24.50"),
            volume=1000000,
        )
        await repo.save(sp)

        latest = await repo.get_latest(company_id)
        assert latest is not None
        assert latest.close_price == Decimal("25.50")

    @pytest.mark.asyncio
    async def test_get_latest_returns_most_recent(self, session, company_id):
        repo = PgStockRepository(session)
        await repo.save_many(
            [
                StockPrice(
                    company_id=company_id,
                    price_date=date(2025, 6, 14),
                    close_price=Decimal("24.00"),
                ),
                StockPrice(
                    company_id=company_id,
                    price_date=date(2025, 6, 15),
                    close_price=Decimal("25.50"),
                ),
            ]
        )

        latest = await repo.get_latest(company_id)
        assert latest.close_price == Decimal("25.50")

    @pytest.mark.asyncio
    async def test_get_by_date_range(self, session, company_id):
        repo = PgStockRepository(session)
        await repo.save_many(
            [
                StockPrice(
                    company_id=company_id,
                    price_date=date(2025, 6, 1),
                    close_price=Decimal("20.00"),
                ),
                StockPrice(
                    company_id=company_id,
                    price_date=date(2025, 6, 15),
                    close_price=Decimal("25.00"),
                ),
                StockPrice(
                    company_id=company_id,
                    price_date=date(2025, 7, 1),
                    close_price=Decimal("30.00"),
                ),
            ]
        )

        date_range = DateRange(start=date(2025, 6, 1), end=date(2025, 6, 30))
        prices = await repo.get_by_date_range(company_id, date_range)

        assert len(prices) == 2
        assert prices[0].close_price == Decimal("20.00")
        assert prices[1].close_price == Decimal("25.00")

    @pytest.mark.asyncio
    async def test_get_latest_no_data(self, session, company_id):
        repo = PgStockRepository(session)
        result = await repo.get_latest(company_id)
        assert result is None


# ─── Patent Repository ────────────────────────────────────────────────────────


class TestPgPatentRepository:
    @pytest.fixture
    async def company_id(self, session):
        repo = PgCompanyRepository(session)
        company = await repo.save(
            Company(name="IonQ", slug="ionq", sector=Sector.PURE_PLAY)
        )
        return company.id

    @pytest.mark.asyncio
    async def test_save_and_get_by_company(self, session, company_id):
        repo = PgPatentRepository(session)
        patent = Patent(
            company_id=company_id,
            patent_number="US12345678",
            title="Quantum Error Correction",
            filing_date=date(2025, 6, 15),
            source=PatentSource.USPTO,
            abstract="A method for error correction",
        )
        await repo.save(patent)

        patents = await repo.get_by_company(company_id)
        assert len(patents) == 1
        assert patents[0].patent_number == "US12345678"
        assert patents[0].source == PatentSource.USPTO

    @pytest.mark.asyncio
    async def test_get_by_date_range(self, session, company_id):
        repo = PgPatentRepository(session)
        await repo.save_many(
            [
                Patent(
                    company_id=company_id,
                    patent_number="P1",
                    title="Patent 1",
                    filing_date=date(2025, 1, 15),
                ),
                Patent(
                    company_id=company_id,
                    patent_number="P2",
                    title="Patent 2",
                    filing_date=date(2025, 6, 15),
                ),
                Patent(
                    company_id=company_id,
                    patent_number="P3",
                    title="Patent 3",
                    filing_date=date(2025, 12, 15),
                ),
            ]
        )

        date_range = DateRange(start=date(2025, 1, 1), end=date(2025, 6, 30))
        patents = await repo.get_by_date_range(company_id, date_range)
        assert len(patents) == 2

    @pytest.mark.asyncio
    async def test_count_by_date_range(self, session, company_id):
        repo = PgPatentRepository(session)
        await repo.save_many(
            [
                Patent(
                    company_id=company_id,
                    patent_number="P1",
                    title="Patent 1",
                    filing_date=date(2025, 3, 1),
                ),
                Patent(
                    company_id=company_id,
                    patent_number="P2",
                    title="Patent 2",
                    filing_date=date(2025, 5, 1),
                ),
                Patent(
                    company_id=company_id,
                    patent_number="P3",
                    title="Patent 3",
                    filing_date=date(2026, 1, 1),
                ),
            ]
        )

        date_range = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))
        count = await repo.count_by_date_range(company_id, date_range)
        assert count == 2


# ─── Score Repository ─────────────────────────────────────────────────────────


class TestPgScoreRepository:
    @pytest.fixture
    async def company_id(self, session):
        repo = PgCompanyRepository(session)
        company = await repo.save(
            Company(name="IonQ", slug="ionq", sector=Sector.PURE_PLAY)
        )
        return company.id

    @pytest.mark.asyncio
    async def test_save_and_get_latest(self, session, company_id):
        repo = PgScoreRepository(session)
        score = QuantumPowerScore(
            company_id=company_id,
            score_date=date(2025, 6, 15),
            stock_momentum=75.0,
            patent_velocity=60.0,
            qubit_progress=80.0,
            funding_strength=65.0,
            news_sentiment=70.0,
            rank=1,
            rank_change=2,
        )
        await repo.save(score)

        latest = await repo.get_latest(company_id)
        assert latest is not None
        assert latest.stock_momentum == 75.0
        assert latest.rank == 1
        assert latest.rank_change == 2

    @pytest.mark.asyncio
    async def test_get_latest_all(self, session):
        company_repo = PgCompanyRepository(session)
        c1 = await company_repo.save(
            Company(name="IonQ", slug="ionq", sector=Sector.PURE_PLAY)
        )
        c2 = await company_repo.save(
            Company(name="D-Wave", slug="d-wave", sector=Sector.PURE_PLAY)
        )

        repo = PgScoreRepository(session)
        await repo.save_many(
            [
                QuantumPowerScore(
                    company_id=c1.id,
                    score_date=date(2025, 6, 1),
                    stock_momentum=50.0,
                    patent_velocity=50.0,
                    qubit_progress=50.0,
                    funding_strength=50.0,
                    news_sentiment=50.0,
                ),
                QuantumPowerScore(
                    company_id=c1.id,
                    score_date=date(2025, 6, 15),
                    stock_momentum=75.0,
                    patent_velocity=60.0,
                    qubit_progress=80.0,
                    funding_strength=65.0,
                    news_sentiment=70.0,
                ),
                QuantumPowerScore(
                    company_id=c2.id,
                    score_date=date(2025, 6, 10),
                    stock_momentum=40.0,
                    patent_velocity=45.0,
                    qubit_progress=55.0,
                    funding_strength=35.0,
                    news_sentiment=60.0,
                ),
            ]
        )

        latest_all = await repo.get_latest_all()
        assert len(latest_all) == 2

        # Should get the most recent per company
        by_company = {s.company_id: s for s in latest_all}
        assert by_company[c1.id].score_date == date(2025, 6, 15)
        assert by_company[c2.id].score_date == date(2025, 6, 10)

    @pytest.mark.asyncio
    async def test_get_by_date_range(self, session, company_id):
        repo = PgScoreRepository(session)
        await repo.save_many(
            [
                QuantumPowerScore(
                    company_id=company_id,
                    score_date=date(2025, 1, 1),
                    stock_momentum=50.0,
                    patent_velocity=50.0,
                    qubit_progress=50.0,
                    funding_strength=50.0,
                    news_sentiment=50.0,
                ),
                QuantumPowerScore(
                    company_id=company_id,
                    score_date=date(2025, 6, 15),
                    stock_momentum=75.0,
                    patent_velocity=60.0,
                    qubit_progress=80.0,
                    funding_strength=65.0,
                    news_sentiment=70.0,
                ),
                QuantumPowerScore(
                    company_id=company_id,
                    score_date=date(2025, 12, 1),
                    stock_momentum=90.0,
                    patent_velocity=70.0,
                    qubit_progress=85.0,
                    funding_strength=75.0,
                    news_sentiment=80.0,
                ),
            ]
        )

        date_range = DateRange(start=date(2025, 5, 1), end=date(2025, 7, 1))
        scores = await repo.get_by_date_range(company_id, date_range)
        assert len(scores) == 1
        assert scores[0].score_date == date(2025, 6, 15)


# ─── News Repository ─────────────────────────────────────────────────────────


class TestPgNewsRepository:
    @pytest.fixture
    async def company_id(self, session):
        repo = PgCompanyRepository(session)
        company = await repo.save(
            Company(name="IonQ", slug="ionq", sector=Sector.PURE_PLAY)
        )
        return company.id

    @pytest.mark.asyncio
    async def test_save_and_get_by_company(self, session, company_id):
        repo = PgNewsRepository(session)
        article = NewsArticle(
            company_id=company_id,
            title="IonQ Breakthrough",
            url="https://example.com/ionq",
            published_at=datetime(2025, 6, 15, 10, 30, tzinfo=UTC),
            source_name="Reuters",
            sentiment=SentimentLabel.BULLISH,
            sentiment_score=Decimal("0.85"),
        )
        await repo.save(article)

        articles = await repo.get_by_company(company_id)
        assert len(articles) == 1
        assert articles[0].title == "IonQ Breakthrough"
        assert articles[0].sentiment == SentimentLabel.BULLISH

    @pytest.mark.asyncio
    async def test_get_by_company_respects_limit(self, session, company_id):
        repo = PgNewsRepository(session)
        await repo.save_many(
            [
                NewsArticle(
                    company_id=company_id,
                    title=f"Article {i}",
                    url=f"https://example.com/{i}",
                    published_at=datetime(2025, 6, i + 1, tzinfo=UTC),
                )
                for i in range(5)
            ]
        )

        articles = await repo.get_by_company(company_id, limit=3)
        assert len(articles) == 3

    @pytest.mark.asyncio
    async def test_save_without_sentiment(self, session, company_id):
        repo = PgNewsRepository(session)
        article = NewsArticle(
            company_id=company_id,
            title="Neutral News",
            url="https://example.com/neutral",
            published_at=datetime(2025, 6, 15, tzinfo=UTC),
        )
        await repo.save(article)

        retrieved = await repo.get_by_company(company_id)
        assert len(retrieved) == 1
        assert retrieved[0].sentiment is None
        assert retrieved[0].sentiment_score is None


# ─── Filing Repository ────────────────────────────────────────────────────────


class TestPgFilingRepository:
    @pytest.fixture
    async def company_id(self, session):
        repo = PgCompanyRepository(session)
        company = await repo.save(
            Company(name="IonQ", slug="ionq", sector=Sector.PURE_PLAY)
        )
        return company.id

    @pytest.mark.asyncio
    async def test_save_and_get_by_company(self, session, company_id):
        repo = PgFilingRepository(session)
        filing = Filing(
            company_id=company_id,
            filing_type=FilingType.FORM_10K,
            filing_date=date(2025, 3, 15),
            description="Annual Report",
            url="https://sec.gov/filing/123",
        )
        await repo.save(filing)

        filings = await repo.get_by_company(company_id)
        assert len(filings) == 1
        assert filings[0].filing_type == FilingType.FORM_10K
        assert filings[0].description == "Annual Report"

    @pytest.mark.asyncio
    async def test_get_by_type(self, session, company_id):
        repo = PgFilingRepository(session)
        await repo.save_many(
            [
                Filing(
                    company_id=company_id,
                    filing_type=FilingType.FORM_10K,
                    filing_date=date(2025, 3, 15),
                ),
                Filing(
                    company_id=company_id,
                    filing_type=FilingType.FORM_10Q,
                    filing_date=date(2025, 6, 15),
                ),
                Filing(
                    company_id=company_id,
                    filing_type=FilingType.FORM_4,
                    filing_date=date(2025, 7, 1),
                ),
                Filing(
                    company_id=company_id,
                    filing_type=FilingType.FORM_4,
                    filing_date=date(2025, 8, 1),
                ),
            ]
        )

        form4s = await repo.get_by_type(company_id, "Form4")
        assert len(form4s) == 2
        assert all(f.filing_type == FilingType.FORM_4 for f in form4s)

    @pytest.mark.asyncio
    async def test_save_many(self, session, company_id):
        repo = PgFilingRepository(session)
        filings = [
            Filing(
                company_id=company_id,
                filing_type=FilingType.FORM_10K,
                filing_date=date(2025, 3, 15),
            ),
            Filing(
                company_id=company_id,
                filing_type=FilingType.FORM_10Q,
                filing_date=date(2025, 6, 15),
            ),
        ]
        saved = await repo.save_many(filings)
        assert len(saved) == 2
        assert all(f.id is not None for f in saved)
