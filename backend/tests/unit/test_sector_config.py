"""Unit tests for SectorConfig domain model."""

import pytest

from src.domain.models.sector_config import DEFAULT_ETF_SECTOR, DEFAULT_QUANTUM_SECTOR, SectorConfig


class TestSectorConfig:
    def test_valid_sector_config(self):
        config = SectorConfig(
            name="test_sector",
            display_name="Test Sector",
            slug="test-sector",
            description="A test sector",
            score_weights={"a": 0.5, "b": 0.5},
        )
        assert config.name == "test_sector"
        assert config.enabled is True

    def test_weights_must_sum_to_one(self):
        with pytest.raises(ValueError, match=r"sum to ~1\.0"):
            SectorConfig(
                name="bad",
                display_name="Bad",
                slug="bad",
                description="Bad weights",
                score_weights={"a": 0.3, "b": 0.3},
            )

    def test_weights_tolerance(self):
        # 0.995 should be accepted (within ±0.01)
        config = SectorConfig(
            name="ok",
            display_name="OK",
            slug="ok",
            description="Close enough",
            score_weights={"a": 0.504, "b": 0.500},
        )
        assert config.name == "ok"

    def test_default_quantum_sector(self):
        assert DEFAULT_QUANTUM_SECTOR.name == "quantum_computing"
        assert DEFAULT_QUANTUM_SECTOR.display_name == "Quantum Computing"
        total = sum(DEFAULT_QUANTUM_SECTOR.score_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_default_quantum_weights(self):
        w = DEFAULT_QUANTUM_SECTOR.score_weights
        assert w["stock_momentum"] == 0.20
        assert w["patent_velocity"] == 0.25
        assert w["qubit_progress"] == 0.20
        assert w["funding_strength"] == 0.20
        assert w["news_sentiment"] == 0.15

    def test_default_etf_sector(self):
        assert DEFAULT_ETF_SECTOR.name == "etf"
        assert DEFAULT_ETF_SECTOR.display_name == "Quantum ETFs"
        total = sum(DEFAULT_ETF_SECTOR.score_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_default_etf_weights(self):
        w = DEFAULT_ETF_SECTOR.score_weights
        assert w["stock_momentum"] == 0.60
        assert w["news_sentiment"] == 0.40
        assert "patent_velocity" not in w
        assert "qubit_progress" not in w
        assert "funding_strength" not in w

    def test_disabled_sector(self):
        config = SectorConfig(
            name="disabled",
            display_name="Disabled",
            slug="disabled",
            description="Not active",
            score_weights={"a": 1.0},
            enabled=False,
        )
        assert config.enabled is False
