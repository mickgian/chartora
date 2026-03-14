"""Domain model for sector configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SectorConfig:
    """Represents a trackable industry sector with scoring weights.

    Each sector defines its own set of metric weights used to calculate
    the composite power score for companies within that sector.
    """

    name: str
    display_name: str
    slug: str
    description: str
    score_weights: dict[str, float]
    enabled: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        """Validate that score weights sum to approximately 1.0."""
        total = sum(self.score_weights.values())
        if abs(total - 1.0) > 0.01:
            msg = (
                f"Score weights must sum to ~1.0 (±0.01), "
                f"got {total:.4f} for sector '{self.name}'"
            )
            raise ValueError(msg)


DEFAULT_QUANTUM_SECTOR = SectorConfig(
    name="quantum_computing",
    display_name="Quantum Computing",
    slug="quantum-computing",
    description=(
        "Rankings and analysis of public quantum computing companies, "
        "big tech quantum divisions, and quantum-focused ETFs."
    ),
    score_weights={
        "stock_momentum": 0.20,
        "patent_velocity": 0.25,
        "qubit_progress": 0.20,
        "funding_strength": 0.20,
        "news_sentiment": 0.15,
    },
    enabled=True,
)
