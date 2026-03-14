"""Unit tests for the Quantum Power Score calculation use case."""

from datetime import date

import pytest

from src.usecases.calculate_score import (
    ScoreInput,
    _normalize_funding_strength,
    _normalize_news_sentiment,
    _normalize_patent_velocity,
    _normalize_qubit_progress,
    _normalize_stock_momentum,
    calculate_score,
)

# ─── Stock Momentum Normalization ──────────────────────────────────────────────


class TestNormalizeStockMomentum:
    def test_all_none_returns_midpoint(self) -> None:
        # None → 0% return → maps to (0+50)/150*100 = 33.33
        result = _normalize_stock_momentum(None, None, None)
        assert result == pytest.approx(33.33, abs=0.01)

    def test_all_zero_returns_midpoint(self) -> None:
        result = _normalize_stock_momentum(0.0, 0.0, 0.0)
        assert result == pytest.approx(33.33, abs=0.01)

    def test_strong_positive(self) -> None:
        # +100% across all windows → (100+50)/150*100 = 100
        result = _normalize_stock_momentum(100.0, 100.0, 100.0)
        assert result == 100.0

    def test_strong_negative(self) -> None:
        # -50% across all → (-50+50)/150*100 = 0
        result = _normalize_stock_momentum(-50.0, -50.0, -50.0)
        assert result == 0.0

    def test_mixed_returns(self) -> None:
        # 30d=20%, 60d=10%, 90d=-5%
        # blended = 20*0.5 + 10*0.3 + (-5)*0.2 = 10+3-1 = 12
        # normalized = (12+50)/150*100 = 41.33
        result = _normalize_stock_momentum(20.0, 10.0, -5.0)
        assert result == pytest.approx(41.33, abs=0.01)

    def test_clamped_below_zero(self) -> None:
        result = _normalize_stock_momentum(-100.0, -100.0, -100.0)
        assert result == 0.0

    def test_clamped_above_100(self) -> None:
        result = _normalize_stock_momentum(200.0, 200.0, 200.0)
        assert result == 100.0


# ─── Patent Velocity Normalization ─────────────────────────────────────────────


class TestNormalizePatentVelocity:
    def test_none_returns_zero(self) -> None:
        assert _normalize_patent_velocity(None) == 0.0

    def test_zero_patents(self) -> None:
        assert _normalize_patent_velocity(0) == 0.0

    def test_one_patent(self) -> None:
        result = _normalize_patent_velocity(1)
        assert 10.0 < result < 20.0

    def test_five_patents(self) -> None:
        result = _normalize_patent_velocity(5)
        assert result == 40.0

    def test_twenty_patents(self) -> None:
        result = _normalize_patent_velocity(20)
        assert result == 70.0

    def test_fifty_patents(self) -> None:
        result = _normalize_patent_velocity(50)
        assert result == 85.0

    def test_hundred_patents(self) -> None:
        result = _normalize_patent_velocity(100)
        assert 85.0 < result <= 100.0

    def test_monotonically_increasing(self) -> None:
        values = [_normalize_patent_velocity(i) for i in range(0, 101)]
        for i in range(1, len(values)):
            assert values[i] >= values[i - 1]


# ─── Qubit Progress Normalization ──────────────────────────────────────────────


class TestNormalizeQubitProgress:
    def test_none_returns_zero(self) -> None:
        assert _normalize_qubit_progress(None) == 0.0

    def test_zero_qubits(self) -> None:
        assert _normalize_qubit_progress(0) == 0.0

    def test_small_qubit_count(self) -> None:
        result = _normalize_qubit_progress(5)
        assert 10.0 < result < 30.0

    def test_medium_qubit_count(self) -> None:
        result = _normalize_qubit_progress(50)
        assert result == 50.0

    def test_hundred_qubits(self) -> None:
        result = _normalize_qubit_progress(100)
        assert result == 70.0

    def test_thousand_qubits(self) -> None:
        result = _normalize_qubit_progress(1000)
        assert result == 90.0

    def test_above_thousand(self) -> None:
        result = _normalize_qubit_progress(5000)
        assert 90.0 < result <= 100.0

    def test_monotonically_increasing(self) -> None:
        test_points = [0, 1, 5, 10, 25, 50, 100, 500, 1000, 5000]
        values = [_normalize_qubit_progress(q) for q in test_points]
        for i in range(1, len(values)):
            assert values[i] >= values[i - 1]


# ─── Funding Strength Normalization ────────────────────────────────────────────


class TestNormalizeFundingStrength:
    def test_none_returns_zero(self) -> None:
        assert _normalize_funding_strength(None, None) == 0.0

    def test_billion_dollar_funding(self) -> None:
        result = _normalize_funding_strength(1_000_000_000.0, None)
        assert result == pytest.approx(70.0, abs=0.01)

    def test_large_recent_round(self) -> None:
        result = _normalize_funding_strength(None, 500_000_000.0)
        assert result == pytest.approx(30.0, abs=0.01)

    def test_both_components(self) -> None:
        result = _normalize_funding_strength(500_000_000.0, 100_000_000.0)
        # total_norm = 50, recent_norm = 20
        # = 50*0.7 + 20*0.3 = 35+6 = 41
        assert result == pytest.approx(41.0, abs=0.01)

    def test_capped_at_100(self) -> None:
        result = _normalize_funding_strength(10_000_000_000.0, 5_000_000_000.0)
        assert result == 100.0


# ─── News Sentiment Normalization ──────────────────────────────────────────────


class TestNormalizeNewsSentiment:
    def test_none_returns_neutral(self) -> None:
        assert _normalize_news_sentiment(None, None) == 50.0

    def test_zero_articles_returns_neutral(self) -> None:
        assert _normalize_news_sentiment(0.8, 0) == 50.0

    def test_strong_positive_many_articles(self) -> None:
        result = _normalize_news_sentiment(1.0, 20)
        assert result == 100.0

    def test_strong_negative_many_articles(self) -> None:
        result = _normalize_news_sentiment(-1.0, 20)
        assert result == 0.0

    def test_neutral_sentiment(self) -> None:
        result = _normalize_news_sentiment(0.0, 10)
        assert result == 50.0

    def test_few_articles_pulled_toward_neutral(self) -> None:
        # With only 2 articles, confidence = 0.2
        # base = (0.8 + 1) / 2 * 100 = 90
        # adjusted = 90 * 0.2 + 50 * 0.8 = 18 + 40 = 58
        result = _normalize_news_sentiment(0.8, 2)
        assert result == pytest.approx(58.0, abs=0.01)


# ─── Full Score Calculation ────────────────────────────────────────────────────


class TestCalculateScore:
    def test_with_all_data(self) -> None:
        score_input = ScoreInput(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_return_30d=20.0,
            stock_return_60d=15.0,
            stock_return_90d=10.0,
            patents_filed_12m=12,
            qubit_count=50,
            total_funding_usd=500_000_000.0,
            recent_round_usd=100_000_000.0,
            avg_sentiment=0.5,
            article_count=10,
        )
        result = calculate_score(score_input)

        assert result.company_id == 1
        assert result.score_date == date(2025, 3, 14)
        assert 0.0 <= result.stock_momentum <= 100.0
        assert 0.0 <= result.patent_velocity <= 100.0
        assert 0.0 <= result.qubit_progress <= 100.0
        assert 0.0 <= result.funding_strength <= 100.0
        assert 0.0 <= result.news_sentiment <= 100.0
        assert 0.0 <= result.total_score <= 100.0

    def test_with_all_none_data(self) -> None:
        score_input = ScoreInput(
            company_id=2,
            score_date=date(2025, 3, 14),
        )
        result = calculate_score(score_input)

        assert result.company_id == 2
        assert result.stock_momentum == pytest.approx(33.33, abs=0.01)
        assert result.patent_velocity == 0.0
        assert result.qubit_progress == 0.0
        assert result.funding_strength == 0.0
        assert result.news_sentiment == 50.0
        assert result.total_score > 0.0  # non-zero due to stock + sentiment defaults

    def test_single_company_edge_case(self) -> None:
        score_input = ScoreInput(
            company_id=99,
            score_date=date(2025, 1, 1),
            stock_return_30d=0.0,
            patents_filed_12m=0,
            qubit_count=0,
            total_funding_usd=0.0,
            avg_sentiment=0.0,
            article_count=0,
        )
        result = calculate_score(score_input)
        assert 0.0 <= result.total_score <= 100.0

    def test_maximum_inputs(self) -> None:
        score_input = ScoreInput(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_return_30d=100.0,
            stock_return_60d=100.0,
            stock_return_90d=100.0,
            patents_filed_12m=200,
            qubit_count=10000,
            total_funding_usd=10_000_000_000.0,
            recent_round_usd=5_000_000_000.0,
            avg_sentiment=1.0,
            article_count=100,
        )
        result = calculate_score(score_input)
        assert result.total_score == 100.0

    def test_score_returns_quantum_power_score_entity(self) -> None:
        score_input = ScoreInput(
            company_id=1,
            score_date=date(2025, 3, 14),
            stock_return_30d=10.0,
            patents_filed_12m=5,
            qubit_count=20,
        )
        result = calculate_score(score_input)
        assert result.rank is None
        assert result.rank_change is None
