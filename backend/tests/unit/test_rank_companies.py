"""Unit tests for the company ranking use case."""

from datetime import date

from src.domain.models.entities import QuantumPowerScore
from src.domain.models.value_objects import TrendDirection
from src.usecases.rank_companies import (
    RankingMetric,
    rank_companies,
)


def _make_score(
    company_id: int,
    stock: float = 50.0,
    patents: float = 50.0,
    qubits: float = 50.0,
    funding: float = 50.0,
    sentiment: float = 50.0,
) -> QuantumPowerScore:
    """Helper to create a QuantumPowerScore."""
    return QuantumPowerScore(
        company_id=company_id,
        score_date=date(2025, 3, 14),
        stock_momentum=stock,
        patent_velocity=patents,
        qubit_progress=qubits,
        funding_strength=funding,
        news_sentiment=sentiment,
    )


def _uniform(cid: int, val: float) -> QuantumPowerScore:
    """All components set to the same value."""
    return _make_score(cid, val, val, val, val, val)


class TestRankCompanies:
    def test_empty_scores(self) -> None:
        result = rank_companies([])
        assert result.count == 0
        assert result.metric == RankingMetric.TOTAL_SCORE

    def test_single_company(self) -> None:
        scores = [_make_score(1)]
        result = rank_companies(scores)
        assert result.count == 1
        assert result.rankings[0].rank == 1
        assert result.rankings[0].company_id == 1

    def test_ranked_by_total_score_descending(self) -> None:
        scores = [
            _uniform(1, 30.0),
            _uniform(2, 80.0),
            _uniform(3, 50.0),
        ]
        result = rank_companies(scores)
        assert [r.company_id for r in result.rankings] == [2, 3, 1]
        assert result.rankings[0].rank == 1
        assert result.rankings[1].rank == 2
        assert result.rankings[2].rank == 3

    def test_rank_by_stock_momentum(self) -> None:
        scores = [
            _make_score(1, stock=90.0),
            _make_score(2, stock=40.0),
            _make_score(3, stock=70.0),
        ]
        result = rank_companies(scores, metric=RankingMetric.STOCK_MOMENTUM)
        assert result.metric == RankingMetric.STOCK_MOMENTUM
        assert [r.company_id for r in result.rankings] == [1, 3, 2]

    def test_rank_by_patent_velocity(self) -> None:
        scores = [
            _make_score(1, patents=20.0),
            _make_score(2, patents=95.0),
        ]
        result = rank_companies(scores, metric=RankingMetric.PATENT_VELOCITY)
        assert result.rankings[0].company_id == 2
        assert result.rankings[0].metric_value == 95.0

    def test_rank_by_qubit_progress(self) -> None:
        scores = [
            _make_score(1, qubits=10.0),
            _make_score(2, qubits=85.0),
        ]
        result = rank_companies(scores, metric=RankingMetric.QUBIT_PROGRESS)
        assert result.rankings[0].company_id == 2

    def test_rank_by_funding_strength(self) -> None:
        scores = [
            _make_score(1, funding=100.0),
            _make_score(2, funding=20.0),
        ]
        result = rank_companies(scores, metric=RankingMetric.FUNDING_STRENGTH)
        assert result.rankings[0].company_id == 1

    def test_rank_by_news_sentiment(self) -> None:
        scores = [
            _make_score(1, sentiment=30.0),
            _make_score(2, sentiment=70.0),
        ]
        result = rank_companies(scores, metric=RankingMetric.NEWS_SENTIMENT)
        assert result.rankings[0].company_id == 2


class TestRankChanges:
    def test_no_previous_scores_gives_none_rank_change(self) -> None:
        scores = [_make_score(1), _make_score(2)]
        result = rank_companies(scores)
        for r in result.rankings:
            assert r.rank_change is None
            assert r.trend == TrendDirection.FLAT

    def test_rank_change_up(self) -> None:
        previous = [_uniform(1, 80.0), _uniform(2, 30.0)]
        current = [_uniform(1, 30.0), _uniform(2, 80.0)]
        result = rank_companies(current, previous_scores=previous)

        # Company 2 was rank 2, now rank 1 → rank_change = +1
        company_2 = next(r for r in result.rankings if r.company_id == 2)
        assert company_2.rank == 1
        assert company_2.rank_change == 1
        assert company_2.trend == TrendDirection.UP

        # Company 1 was rank 1, now rank 2 → rank_change = -1
        company_1 = next(r for r in result.rankings if r.company_id == 1)
        assert company_1.rank == 2
        assert company_1.rank_change == -1
        assert company_1.trend == TrendDirection.DOWN

    def test_rank_no_change(self) -> None:
        scores = [_uniform(1, 80.0), _uniform(2, 50.0)]
        result = rank_companies(scores, previous_scores=scores)
        for r in result.rankings:
            assert r.rank_change == 0
            assert r.trend == TrendDirection.FLAT

    def test_new_company_has_none_rank_change(self) -> None:
        previous = [_make_score(1)]
        current = [_make_score(1), _make_score(2)]
        result = rank_companies(current, previous_scores=previous)
        company_2 = next(r for r in result.rankings if r.company_id == 2)
        assert company_2.rank_change is None


class TestRankingResult:
    def test_top_n(self) -> None:
        scores = [_make_score(i, stock=float(100 - i * 10)) for i in range(1, 6)]
        result = rank_companies(scores, metric=RankingMetric.STOCK_MOMENTUM)
        top3 = result.top(3)
        assert len(top3) == 3
        assert top3[0].rank == 1

    def test_top_n_larger_than_count(self) -> None:
        scores = [_make_score(1)]
        result = rank_companies(scores)
        top5 = result.top(5)
        assert len(top5) == 1

    def test_count(self) -> None:
        scores = [_make_score(i) for i in range(1, 8)]
        result = rank_companies(scores)
        assert result.count == 7
