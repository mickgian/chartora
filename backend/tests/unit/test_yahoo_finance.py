"""Unit tests for the Yahoo Finance adapter."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.domain.models.value_objects import DateRange
from src.infrastructure.yahoo_finance import YahooFinanceAdapter


@pytest.fixture
def adapter():
    return YahooFinanceAdapter()


def _make_history_df(rows: list[dict]) -> pd.DataFrame:
    """Create a DataFrame mimicking yfinance history output."""
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.pop("Date"))
    return df


class TestYahooFinanceCurrentPrice:
    @pytest.mark.asyncio
    async def test_fetch_current_price_returns_stock_price(self, adapter):
        mock_df = _make_history_df(
            [
                {
                    "Date": "2026-03-10",
                    "Open": 25.50,
                    "High": 26.00,
                    "Low": 25.00,
                    "Close": 25.75,
                    "Volume": 1000000,
                },
                {
                    "Date": "2026-03-11",
                    "Open": 25.80,
                    "High": 26.50,
                    "Low": 25.60,
                    "Close": 26.10,
                    "Volume": 1200000,
                },
            ]
        )

        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = mock_df
            result = await adapter.fetch_current_price("IONQ")

        assert result is not None
        assert result.close_price == Decimal("26.10")
        assert result.open_price == Decimal("25.80")
        assert result.high_price == Decimal("26.50")
        assert result.low_price == Decimal("25.60")
        assert result.volume == 1200000
        assert result.price_date == date(2026, 3, 11)
        assert result.company_id == 0  # Caller must set

    @pytest.mark.asyncio
    async def test_fetch_current_price_empty_history(self, adapter):
        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = pd.DataFrame()
            result = await adapter.fetch_current_price("INVALID")

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_current_price_handles_exception(self, adapter):
        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = Exception("Network error")
            result = await adapter.fetch_current_price("IONQ")

        assert result is None


class TestYahooFinanceHistory:
    @pytest.mark.asyncio
    async def test_fetch_history_returns_prices(self, adapter):
        mock_df = _make_history_df(
            [
                {
                    "Date": "2026-01-01",
                    "Open": 20.0,
                    "High": 21.0,
                    "Low": 19.0,
                    "Close": 20.5,
                    "Volume": 500000,
                },
                {
                    "Date": "2026-01-02",
                    "Open": 20.5,
                    "High": 22.0,
                    "Low": 20.0,
                    "Close": 21.5,
                    "Volume": 600000,
                },
            ]
        )
        date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 31))

        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = mock_df
            result = await adapter.fetch_history("IONQ", date_range)

        assert len(result) == 2
        assert result[0].close_price == Decimal("20.5")
        assert result[1].close_price == Decimal("21.5")

    @pytest.mark.asyncio
    async def test_fetch_history_empty(self, adapter):
        date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 31))

        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = pd.DataFrame()
            result = await adapter.fetch_history("IONQ", date_range)

        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_history_handles_exception(self, adapter):
        date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 31))

        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = Exception("Error")
            result = await adapter.fetch_history("IONQ", date_range)

        assert result == []


class TestYahooFinanceMarketCap:
    @pytest.mark.asyncio
    async def test_fetch_market_cap(self, adapter):
        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.info = {"marketCap": 5_000_000_000}
            result = await adapter.fetch_market_cap("IONQ")

        assert result == 5_000_000_000

    @pytest.mark.asyncio
    async def test_fetch_market_cap_missing(self, adapter):
        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.info = {}
            result = await adapter.fetch_market_cap("IONQ")

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_market_cap_handles_exception(self, adapter):
        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.info = MagicMock(side_effect=Exception("Error"))
            mock_ticker.return_value.info.__getitem__ = MagicMock(
                side_effect=Exception("Error")
            )
            # Force an exception by making the property raise
            type(mock_ticker.return_value).info = property(
                lambda self: (_ for _ in ()).throw(Exception("Error"))
            )
            result = await adapter.fetch_market_cap("IONQ")

        assert result is None


class TestYahooFinancePerformance:
    @pytest.mark.asyncio
    async def test_fetch_performance(self, adapter):
        mock_df = _make_history_df(
            [
                {
                    "Date": "2025-12-14",
                    "Open": 20.0,
                    "High": 21.0,
                    "Low": 19.0,
                    "Close": 20.0,
                    "Volume": 500000,
                },
                {
                    "Date": "2026-03-14",
                    "Open": 25.0,
                    "High": 26.0,
                    "Low": 24.0,
                    "Close": 25.0,
                    "Volume": 600000,
                },
            ]
        )

        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = mock_df
            result = await adapter.fetch_performance("IONQ", 90)

        assert result is not None
        assert result == 25.0  # (25 - 20) / 20 * 100

    @pytest.mark.asyncio
    async def test_fetch_performance_empty(self, adapter):
        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = pd.DataFrame()
            result = await adapter.fetch_performance("IONQ", 30)

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_performance_handles_exception(self, adapter):
        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.side_effect = Exception("Error")
            result = await adapter.fetch_performance("IONQ", 30)

        assert result is None


class TestDataTransformation:
    def test_get_current_price_static(self):
        """Test the static helper directly for data transformation."""
        mock_df = _make_history_df(
            [
                {
                    "Date": "2026-03-10",
                    "Open": 10.1234,
                    "High": 10.5678,
                    "Low": 9.8765,
                    "Close": 10.3456,
                    "Volume": 999999,
                },
            ]
        )

        with patch("src.infrastructure.yahoo_finance.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = mock_df
            result = YahooFinanceAdapter._get_current_price("TEST")

        assert result is not None
        assert result.close_price == Decimal("10.3456")
        assert result.open_price == Decimal("10.1234")
        assert result.high_price == Decimal("10.5678")
        assert result.low_price == Decimal("9.8765")
