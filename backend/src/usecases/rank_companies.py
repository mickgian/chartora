"""Use case: Rank companies by Quantum Power Score or individual metrics.

Supports ranking by total score or by any single component metric.
Calculates rank changes relative to previous rankings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from src.domain.models.value_objects import TrendDirection

if TYPE_CHECKING:
    from src.domain.models.entities import QuantumPowerScore


class RankingMetric(StrEnum):
    """Available metrics to rank companies by."""

    TOTAL_SCORE = "total_score"
    STOCK_MOMENTUM = "stock_momentum"
    PATENT_VELOCITY = "patent_velocity"
    QUBIT_PROGRESS = "qubit_progress"
    FUNDING_STRENGTH = "funding_strength"
    NEWS_SENTIMENT = "news_sentiment"


@dataclass
class RankedCompany:
    """A company with its rank and score details."""

    company_id: int
    rank: int
    score: QuantumPowerScore
    metric_value: float
    rank_change: int | None = None

    @property
    def trend(self) -> TrendDirection:
        """Determine trend direction from rank change."""
        if self.rank_change is None or self.rank_change == 0:
            return TrendDirection.FLAT
        return TrendDirection.UP if self.rank_change > 0 else TrendDirection.DOWN


@dataclass
class RankingResult:
    """The result of ranking companies."""

    metric: RankingMetric
    rankings: list[RankedCompany] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.rankings)

    def top(self, n: int) -> list[RankedCompany]:
        """Get top N ranked companies."""
        return self.rankings[:n]


def _get_metric_value(score: QuantumPowerScore, metric: RankingMetric) -> float:
    """Extract the value of a given metric from a score."""
    metric_map: dict[RankingMetric, str] = {
        RankingMetric.TOTAL_SCORE: "total_score",
        RankingMetric.STOCK_MOMENTUM: "stock_momentum",
        RankingMetric.PATENT_VELOCITY: "patent_velocity",
        RankingMetric.QUBIT_PROGRESS: "qubit_progress",
        RankingMetric.FUNDING_STRENGTH: "funding_strength",
        RankingMetric.NEWS_SENTIMENT: "news_sentiment",
    }
    return float(getattr(score, metric_map[metric]))


def rank_companies(
    scores: list[QuantumPowerScore],
    metric: RankingMetric = RankingMetric.TOTAL_SCORE,
    previous_scores: list[QuantumPowerScore] | None = None,
) -> RankingResult:
    """Rank companies by a given metric.

    Args:
        scores: Current scores for all companies to rank.
        metric: The metric to rank by (default: total_score).
        previous_scores: Optional previous scores to calculate rank changes.

    Returns:
        A RankingResult with companies sorted by the chosen metric (descending).
    """
    if not scores:
        return RankingResult(metric=metric)

    # Sort by metric value descending
    sorted_scores = sorted(
        scores,
        key=lambda s: _get_metric_value(s, metric),
        reverse=True,
    )

    # Build previous rank lookup if available
    previous_ranks: dict[int, int] = {}
    if previous_scores:
        prev_sorted = sorted(
            previous_scores,
            key=lambda s: _get_metric_value(s, metric),
            reverse=True,
        )
        for i, s in enumerate(prev_sorted, start=1):
            previous_ranks[s.company_id] = i

    rankings: list[RankedCompany] = []
    for i, score in enumerate(sorted_scores, start=1):
        rank_change: int | None = None
        if previous_ranks:
            prev_rank = previous_ranks.get(score.company_id)
            if prev_rank is not None:
                # Positive means moved up (lower rank number = better)
                rank_change = prev_rank - i

        rankings.append(
            RankedCompany(
                company_id=score.company_id,
                rank=i,
                score=score,
                metric_value=_get_metric_value(score, metric),
                rank_change=rank_change,
            )
        )

    return RankingResult(metric=metric, rankings=rankings)
