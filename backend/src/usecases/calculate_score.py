"""Use case: Calculate the Quantum Power Score for a company.

This module implements the scoring algorithm that produces a composite score
from five normalized components: stock momentum, patent velocity, qubit progress,
funding strength, and news sentiment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.domain.models.entities import QuantumPowerScore

if TYPE_CHECKING:
    from datetime import date


@dataclass(frozen=True)
class ScoreInput:
    """Raw metric inputs for score calculation.

    All values are raw (un-normalized). The calculator normalizes them
    to a 0-100 scale before weighting.
    """

    company_id: int
    score_date: date

    # Stock momentum: percentage returns over 30/60/90 days
    stock_return_30d: float | None = None
    stock_return_60d: float | None = None
    stock_return_90d: float | None = None

    # Patent velocity: number of patents filed in the last 12 months
    patents_filed_12m: int | None = None

    # Qubit progress: latest announced qubit count
    qubit_count: int | None = None

    # Funding strength: total raised (in USD) + recent round amount
    total_funding_usd: float | None = None
    recent_round_usd: float | None = None

    # News sentiment: average sentiment score (-1 to +1 scale)
    avg_sentiment: float | None = None
    article_count: int | None = None


def _normalize_stock_momentum(
    return_30d: float | None,
    return_60d: float | None,
    return_90d: float | None,
) -> float:
    """Normalize stock momentum to 0-100.

    Blends 30/60/90 day returns with weights 50%/30%/20%.
    Maps a return range of -50% to +100% onto 0-100.
    Missing values are treated as 0% return.
    """
    r30 = return_30d if return_30d is not None else 0.0
    r60 = return_60d if return_60d is not None else 0.0
    r90 = return_90d if return_90d is not None else 0.0

    blended = r30 * 0.5 + r60 * 0.3 + r90 * 0.2

    # Map [-50, +100] → [0, 100]
    normalized = ((blended + 50.0) / 150.0) * 100.0
    return max(0.0, min(100.0, normalized))


def _normalize_patent_velocity(patents_filed: int | None) -> float:
    """Normalize patent velocity to 0-100.

    Uses a logarithmic-like scale:
    0 patents → 0, 1-5 → 10-40, 6-20 → 40-70, 21-50 → 70-85, 50+ → 85-100.
    """
    count = patents_filed if patents_filed is not None else 0
    if count <= 0:
        return 0.0
    if count <= 5:
        return 10.0 + (count / 5.0) * 30.0
    if count <= 20:
        return 40.0 + ((count - 5) / 15.0) * 30.0
    if count <= 50:
        return 70.0 + ((count - 20) / 30.0) * 15.0
    return min(100.0, 85.0 + ((count - 50) / 100.0) * 15.0)


def _normalize_qubit_progress(qubit_count: int | None) -> float:
    """Normalize qubit count to 0-100.

    Scale: 0 → 0, 1-10 → 10-30, 11-50 → 30-50, 51-100 → 50-70,
    101-1000 → 70-90, 1000+ → 90-100.
    """
    qubits = qubit_count if qubit_count is not None else 0
    if qubits <= 0:
        return 0.0
    if qubits <= 10:
        return 10.0 + (qubits / 10.0) * 20.0
    if qubits <= 50:
        return 30.0 + ((qubits - 10) / 40.0) * 20.0
    if qubits <= 100:
        return 50.0 + ((qubits - 50) / 50.0) * 20.0
    if qubits <= 1000:
        return 70.0 + ((qubits - 100) / 900.0) * 20.0
    return min(100.0, 90.0 + ((qubits - 1000) / 9000.0) * 10.0)


def _normalize_funding_strength(
    total_funding_usd: float | None,
    recent_round_usd: float | None,
) -> float:
    """Normalize funding strength to 0-100.

    Blends total funding (70% weight) and recent round (30% weight).
    Total funding scale: $0 → 0, $1B+ → 100
    Recent round scale: $0 → 0, $500M+ → 100
    """
    total = total_funding_usd if total_funding_usd is not None else 0.0
    recent = recent_round_usd if recent_round_usd is not None else 0.0

    total_norm = min(100.0, (total / 1_000_000_000.0) * 100.0)
    recent_norm = min(100.0, (recent / 500_000_000.0) * 100.0)

    return max(0.0, min(100.0, total_norm * 0.7 + recent_norm * 0.3))


def _normalize_news_sentiment(
    avg_sentiment: float | None,
    article_count: int | None,
) -> float:
    """Normalize news sentiment to 0-100.

    Maps average sentiment from [-1, +1] to [0, 100].
    Applies a confidence adjustment based on article count:
    fewer articles → score pulled toward 50 (neutral).
    """
    sentiment = avg_sentiment if avg_sentiment is not None else 0.0
    count = article_count if article_count is not None else 0

    # Map [-1, 1] → [0, 100]
    base_score = (sentiment + 1.0) / 2.0 * 100.0

    # Confidence factor: converges to 1.0 as article count increases
    if count <= 0:
        return 50.0  # No articles → neutral
    confidence = min(1.0, count / 10.0)

    # Blend base score with neutral (50) based on confidence
    adjusted = base_score * confidence + 50.0 * (1.0 - confidence)
    return max(0.0, min(100.0, adjusted))


def calculate_score(score_input: ScoreInput) -> QuantumPowerScore:
    """Calculate the Quantum Power Score from raw metric inputs.

    Args:
        score_input: Raw metric data for a single company on a given date.

    Returns:
        A QuantumPowerScore entity with all components normalized to 0-100.
    """
    stock_momentum = round(
        _normalize_stock_momentum(
            score_input.stock_return_30d,
            score_input.stock_return_60d,
            score_input.stock_return_90d,
        ),
        2,
    )
    patent_velocity = round(
        _normalize_patent_velocity(score_input.patents_filed_12m), 2
    )
    qubit_progress = round(_normalize_qubit_progress(score_input.qubit_count), 2)
    funding_strength = round(
        _normalize_funding_strength(
            score_input.total_funding_usd,
            score_input.recent_round_usd,
        ),
        2,
    )
    news_sentiment = round(
        _normalize_news_sentiment(
            score_input.avg_sentiment,
            score_input.article_count,
        ),
        2,
    )

    return QuantumPowerScore(
        company_id=score_input.company_id,
        score_date=score_input.score_date,
        stock_momentum=stock_momentum,
        patent_velocity=patent_velocity,
        qubit_progress=qubit_progress,
        funding_strength=funding_strength,
        news_sentiment=news_sentiment,
    )
