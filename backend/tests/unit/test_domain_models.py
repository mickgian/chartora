"""Unit tests for domain models and value objects."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from src.domain.models import (
    Company,
    DateRange,
    Filing,
    FilingType,
    FundingRound,
    NewsArticle,
    Patent,
    PatentSource,
    QuantumPowerScore,
    ScoreComponent,
    Sector,
    SentimentLabel,
    StockPrice,
    Ticker,
    TrendDirection,
)

# ─── Ticker ────────────────────────────────────────────────────────────────────


class TestTicker:
    def test_valid_ticker(self) -> None:
        t = Ticker("IONQ")
        assert t.symbol == "IONQ"
        assert str(t) == "IONQ"

    def test_ticker_uppercased(self) -> None:
        t = Ticker("ionq")
        assert t.symbol == "IONQ"

    def test_empty_ticker_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            Ticker("")

    def test_ticker_with_digits(self) -> None:
        t = Ticker("6702")
        assert t.symbol == "6702"

    def test_ticker_with_exchange_suffix(self) -> None:
        t = Ticker("ONE.V")
        assert t.symbol == "ONE.V"

    def test_ticker_numeric_with_exchange_suffix(self) -> None:
        t = Ticker("688027.SS")
        assert t.symbol == "688027.SS"

    def test_ticker_invalid_double_dot_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid ticker"):
            Ticker("ONE..V")

    def test_ticker_invalid_trailing_dot_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid ticker"):
            Ticker("ONE.")

    def test_ticker_invalid_special_chars_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid ticker"):
            Ticker("ION@Q")

    def test_ticker_is_frozen(self) -> None:
        t = Ticker("IONQ")
        with pytest.raises(AttributeError):
            t.symbol = "QBTS"  # type: ignore[misc]


# ─── ScoreComponent ────────────────────────────────────────────────────────────


class TestScoreComponent:
    def test_valid_component(self) -> None:
        sc = ScoreComponent(
            name="patents",
            raw_value=42.0,
            normalized_value=75.0,
            weight=0.25,
        )
        assert sc.weighted_value == 75.0 * 0.25

    def test_normalized_value_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="between 0 and 100"):
            ScoreComponent(name="x", raw_value=0, normalized_value=101.0, weight=0.5)

    def test_weight_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="between 0 and 1"):
            ScoreComponent(name="x", raw_value=0, normalized_value=50.0, weight=1.5)

    def test_zero_values(self) -> None:
        sc = ScoreComponent(name="x", raw_value=0, normalized_value=0.0, weight=0.0)
        assert sc.weighted_value == 0.0

    def test_max_values(self) -> None:
        sc = ScoreComponent(name="x", raw_value=999, normalized_value=100.0, weight=1.0)
        assert sc.weighted_value == 100.0


# ─── DateRange ─────────────────────────────────────────────────────────────────


class TestDateRange:
    def test_valid_range(self) -> None:
        dr = DateRange(start=date(2025, 1, 1), end=date(2025, 1, 31))
        assert dr.days == 31

    def test_single_day_range(self) -> None:
        dr = DateRange(start=date(2025, 6, 15), end=date(2025, 6, 15))
        assert dr.days == 1

    def test_inverted_range_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be after"):
            DateRange(start=date(2025, 12, 31), end=date(2025, 1, 1))

    def test_contains(self) -> None:
        dr = DateRange(start=date(2025, 1, 1), end=date(2025, 1, 31))
        assert dr.contains(date(2025, 1, 15))
        assert dr.contains(date(2025, 1, 1))
        assert dr.contains(date(2025, 1, 31))
        assert not dr.contains(date(2025, 2, 1))

    def test_frozen(self) -> None:
        dr = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))
        with pytest.raises(AttributeError):
            dr.start = date(2024, 1, 1)  # type: ignore[misc]


# ─── Company ───────────────────────────────────────────────────────────────────


class TestCompany:
    def test_valid_company(self) -> None:
        c = Company(
            name="IonQ",
            slug="ionq",
            sector=Sector.PURE_PLAY,
            ticker=Ticker("IONQ"),
        )
        assert c.name == "IonQ"
        assert c.ticker is not None
        assert c.ticker.symbol == "IONQ"

    def test_company_without_ticker(self) -> None:
        c = Company(
            name="Quantum Startup",
            slug="quantum-startup",
            sector=Sector.PURE_PLAY,
        )
        assert c.ticker is None

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            Company(name="", slug="test", sector=Sector.PURE_PLAY)

    def test_empty_slug_raises(self) -> None:
        with pytest.raises(ValueError, match="slug cannot be empty"):
            Company(name="Test", slug="", sector=Sector.PURE_PLAY)

    def test_etf_company(self) -> None:
        c = Company(
            name="Defiance Quantum ETF",
            slug="defiance-quantum-etf",
            sector=Sector.ETF,
            ticker=Ticker("QTUM"),
            is_etf=True,
        )
        assert c.is_etf is True
        assert c.sector == Sector.ETF


# ─── StockPrice ────────────────────────────────────────────────────────────────


class TestStockPrice:
    def test_valid_stock_price(self) -> None:
        sp = StockPrice(
            company_id=1,
            price_date=date(2025, 3, 14),
            close_price=Decimal("25.50"),
            open_price=Decimal("24.00"),
            high_price=Decimal("26.00"),
            low_price=Decimal("23.50"),
            volume=1_000_000,
            market_cap=5_000_000_000,
        )
        assert sp.close_price == Decimal("25.50")

    def test_minimal_stock_price(self) -> None:
        sp = StockPrice(
            company_id=1,
            price_date=date(2025, 1, 1),
            close_price=Decimal("10.00"),
        )
        assert sp.open_price is None
        assert sp.volume is None

    def test_negative_price_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            StockPrice(
                company_id=1,
                price_date=date(2025, 1, 1),
                close_price=Decimal("-1.00"),
            )


# ─── Patent ────────────────────────────────────────────────────────────────────


class TestPatent:
    def test_valid_patent(self) -> None:
        p = Patent(
            company_id=1,
            patent_number="US12345678",
            title="Quantum Error Correction Method",
            filing_date=date(2025, 1, 15),
            source=PatentSource.USPTO,
        )
        assert p.patent_number == "US12345678"

    def test_empty_patent_number_raises(self) -> None:
        with pytest.raises(ValueError, match="Patent number cannot be empty"):
            Patent(
                company_id=1,
                patent_number="",
                title="Test",
                filing_date=date(2025, 1, 1),
            )

    def test_empty_title_raises(self) -> None:
        with pytest.raises(ValueError, match="Patent title cannot be empty"):
            Patent(
                company_id=1,
                patent_number="US123",
                title="",
                filing_date=date(2025, 1, 1),
            )

    def test_epo_patent(self) -> None:
        p = Patent(
            company_id=1,
            patent_number="EP1234567",
            title="Qubit Control",
            filing_date=date(2025, 2, 1),
            source=PatentSource.EPO,
        )
        assert p.source == PatentSource.EPO


# ─── FundingRound ──────────────────────────────────────────────────────────────


class TestFundingRound:
    def test_valid_funding(self) -> None:
        f = FundingRound(
            company_id=1,
            round_date=date(2025, 6, 1),
            amount=Decimal("50000000"),
            round_type="Series C",
        )
        assert f.amount == Decimal("50000000")

    def test_negative_amount_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            FundingRound(
                company_id=1,
                round_date=date(2025, 1, 1),
                amount=Decimal("-100"),
            )


# ─── NewsArticle ───────────────────────────────────────────────────────────────


class TestNewsArticle:
    def test_valid_article(self) -> None:
        a = NewsArticle(
            company_id=1,
            title="IonQ Reaches 100 Qubits",
            url="https://example.com/article",
            published_at=datetime(2025, 3, 14, 12, 0, 0),
            sentiment=SentimentLabel.BULLISH,
            sentiment_score=Decimal("0.85"),
        )
        assert a.sentiment == SentimentLabel.BULLISH

    def test_empty_title_raises(self) -> None:
        with pytest.raises(ValueError, match="title cannot be empty"):
            NewsArticle(
                company_id=1,
                title="",
                url="https://example.com",
                published_at=datetime(2025, 1, 1),
            )

    def test_empty_url_raises(self) -> None:
        with pytest.raises(ValueError, match="URL cannot be empty"):
            NewsArticle(
                company_id=1,
                title="Test",
                url="",
                published_at=datetime(2025, 1, 1),
            )


# ─── Filing ────────────────────────────────────────────────────────────────────


class TestFiling:
    def test_valid_filing(self) -> None:
        f = Filing(
            company_id=1,
            filing_type=FilingType.FORM_10K,
            filing_date=date(2025, 3, 1),
            description="Annual report",
        )
        assert f.filing_type == FilingType.FORM_10K


# ─── QuantumPowerScore ─────────────────────────────────────────────────────────


class TestQuantumPowerScore:
    def test_total_score_calculation(self) -> None:
        score = QuantumPowerScore(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_momentum=80.0,
            patent_velocity=60.0,
            qubit_progress=70.0,
            funding_strength=50.0,
            news_sentiment=90.0,
        )
        expected = 80.0 * 0.20 + 60.0 * 0.25 + 70.0 * 0.20 + 50.0 * 0.20 + 90.0 * 0.15
        assert score.total_score == round(expected, 2)

    def test_all_zeros(self) -> None:
        score = QuantumPowerScore(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_momentum=0.0,
            patent_velocity=0.0,
            qubit_progress=0.0,
            funding_strength=0.0,
            news_sentiment=0.0,
        )
        assert score.total_score == 0.0

    def test_all_max(self) -> None:
        score = QuantumPowerScore(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_momentum=100.0,
            patent_velocity=100.0,
            qubit_progress=100.0,
            funding_strength=100.0,
            news_sentiment=100.0,
        )
        assert score.total_score == 100.0

    def test_component_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="between 0 and 100"):
            QuantumPowerScore(
                company_id=1,
                score_date=date(2025, 3, 14),
                stock_momentum=110.0,
                patent_velocity=50.0,
                qubit_progress=50.0,
                funding_strength=50.0,
                news_sentiment=50.0,
            )

    def test_negative_component_raises(self) -> None:
        with pytest.raises(ValueError, match="between 0 and 100"):
            QuantumPowerScore(
                company_id=1,
                score_date=date(2025, 3, 14),
                stock_momentum=-5.0,
                patent_velocity=50.0,
                qubit_progress=50.0,
                funding_strength=50.0,
                news_sentiment=50.0,
            )

    def test_custom_etf_weights(self) -> None:
        """ETFs use only stock_momentum (60%) and news_sentiment (40%)."""
        score = QuantumPowerScore(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_momentum=80.0,
            patent_velocity=0.0,
            qubit_progress=0.0,
            funding_strength=0.0,
            news_sentiment=70.0,
            score_weights={"stock_momentum": 0.60, "news_sentiment": 0.40},
        )
        expected = 80.0 * 0.60 + 70.0 * 0.40
        assert score.total_score == round(expected, 2)

    def test_custom_weights_ignore_zero_metrics(self) -> None:
        """With ETF weights, zero patents/qubits/funding don't drag score down."""
        etf_score = QuantumPowerScore(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_momentum=80.0,
            patent_velocity=0.0,
            qubit_progress=0.0,
            funding_strength=0.0,
            news_sentiment=70.0,
            score_weights={"stock_momentum": 0.60, "news_sentiment": 0.40},
        )
        company_score = QuantumPowerScore(
            company_id=2,
            score_date=date(2025, 3, 14),
            stock_momentum=80.0,
            patent_velocity=0.0,
            qubit_progress=0.0,
            funding_strength=0.0,
            news_sentiment=70.0,
        )
        # ETF score should be much higher since zeros are not weighted
        assert etf_score.total_score > company_score.total_score

    def test_trend_up(self) -> None:
        score = QuantumPowerScore(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_momentum=50.0,
            patent_velocity=50.0,
            qubit_progress=50.0,
            funding_strength=50.0,
            news_sentiment=50.0,
            rank_change=3,
        )
        assert score.trend == TrendDirection.UP

    def test_trend_down(self) -> None:
        score = QuantumPowerScore(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_momentum=50.0,
            patent_velocity=50.0,
            qubit_progress=50.0,
            funding_strength=50.0,
            news_sentiment=50.0,
            rank_change=-2,
        )
        assert score.trend == TrendDirection.DOWN

    def test_trend_flat_zero(self) -> None:
        score = QuantumPowerScore(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_momentum=50.0,
            patent_velocity=50.0,
            qubit_progress=50.0,
            funding_strength=50.0,
            news_sentiment=50.0,
            rank_change=0,
        )
        assert score.trend == TrendDirection.FLAT

    def test_trend_flat_none(self) -> None:
        score = QuantumPowerScore(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_momentum=50.0,
            patent_velocity=50.0,
            qubit_progress=50.0,
            funding_strength=50.0,
            news_sentiment=50.0,
        )
        assert score.trend == TrendDirection.FLAT

    def test_weights_sum_to_one(self) -> None:
        total_weight = (
            QuantumPowerScore.WEIGHT_STOCK_MOMENTUM
            + QuantumPowerScore.WEIGHT_PATENT_VELOCITY
            + QuantumPowerScore.WEIGHT_QUBIT_PROGRESS
            + QuantumPowerScore.WEIGHT_FUNDING_STRENGTH
            + QuantumPowerScore.WEIGHT_NEWS_SENTIMENT
        )
        assert total_weight == pytest.approx(1.0)
