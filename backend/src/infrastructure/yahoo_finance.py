"""Yahoo Finance adapter for fetching stock data.

Implements the StockDataSource interface using the yfinance library.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import yfinance as yf

from src.domain.interfaces.data_sources import StockDataSource
from src.domain.models.entities import StockPrice

if TYPE_CHECKING:
    from src.domain.models.value_objects import DateRange

logger = logging.getLogger(__name__)


class YahooFinanceAdapter(StockDataSource):
    """Fetches stock price data from Yahoo Finance via the yfinance library."""

    async def fetch_current_price(self, ticker: str) -> StockPrice | None:
        """Fetch the most recent stock price for a ticker."""
        try:
            data: StockPrice | None = await self._run_sync(
                self._get_current_price, ticker
            )
            return data
        except Exception:
            logger.exception("Error fetching current price for %s", ticker)
            return None

    async def fetch_history(
        self, ticker: str, date_range: DateRange
    ) -> list[StockPrice]:
        """Fetch historical stock prices for a ticker within a date range."""
        try:
            prices: list[StockPrice] = await self._run_sync(
                self._get_history, ticker, date_range
            )
            return prices
        except Exception:
            logger.exception("Error fetching history for %s", ticker)
            return []

    async def fetch_market_cap(self, ticker: str) -> int | None:
        """Fetch the current market capitalization for a ticker."""
        try:
            cap: int | None = await self._run_sync(
                self._get_market_cap, ticker
            )
            return cap
        except Exception:
            logger.exception("Error fetching market cap for %s", ticker)
            return None

    async def fetch_performance(
        self, ticker: str, days: int
    ) -> float | None:
        """Fetch stock performance (% change) over N days."""
        try:
            perf: float | None = await self._run_sync(
                self._get_performance, ticker, days
            )
            return perf
        except Exception:
            logger.exception(
                "Error fetching %d-day performance for %s", days, ticker
            )
            return None

    @staticmethod
    async def _run_sync(fn: Any, *args: Any) -> Any:
        """Run a synchronous function in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fn, *args)

    @staticmethod
    def _get_current_price(ticker: str) -> StockPrice | None:
        """Synchronous helper to get current price via yfinance."""
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty:
            return None

        latest = hist.iloc[-1]
        price_date = hist.index[-1].date()

        return StockPrice(
            company_id=0,  # Caller must set the correct company_id
            price_date=price_date,
            close_price=Decimal(str(round(latest["Close"], 4))),
            open_price=Decimal(str(round(latest["Open"], 4))),
            high_price=Decimal(str(round(latest["High"], 4))),
            low_price=Decimal(str(round(latest["Low"], 4))),
            volume=int(latest["Volume"]),
            market_cap=None,
        )

    @staticmethod
    def _get_history(ticker: str, date_range: DateRange) -> list[StockPrice]:
        """Synchronous helper to get historical prices via yfinance."""
        stock = yf.Ticker(ticker)
        # yfinance end date is exclusive, so add one day
        end_date = date_range.end + timedelta(days=1)
        hist = stock.history(
            start=date_range.start.isoformat(),
            end=end_date.isoformat(),
        )
        if hist.empty:
            return []

        prices: list[StockPrice] = []
        for idx, row in hist.iterrows():
            price_date: date = idx.date()
            prices.append(
                StockPrice(
                    company_id=0,
                    price_date=price_date,
                    close_price=Decimal(str(round(row["Close"], 4))),
                    open_price=Decimal(str(round(row["Open"], 4))),
                    high_price=Decimal(str(round(row["High"], 4))),
                    low_price=Decimal(str(round(row["Low"], 4))),
                    volume=int(row["Volume"]),
                )
            )
        return prices

    @staticmethod
    def _get_market_cap(ticker: str) -> int | None:
        """Synchronous helper to get market cap via yfinance."""
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get("marketCap")
        if market_cap is None:
            return None
        return int(market_cap)

    @staticmethod
    def _get_performance(ticker: str, days: int) -> float | None:
        """Synchronous helper to calculate percentage change over N days."""
        stock = yf.Ticker(ticker)
        end = date.today()
        # Fetch extra days to account for weekends/holidays
        start = end - timedelta(days=int(days * 1.5) + 5)
        hist = stock.history(
            start=start.isoformat(),
            end=end.isoformat(),
        )
        if hist.empty or len(hist) < 2:
            return None

        # Find the price closest to N days ago
        target_date = end - timedelta(days=days)
        past_prices = hist[hist.index.date <= target_date]
        if past_prices.empty:
            past_prices = hist.iloc[:1]

        start_price = float(past_prices.iloc[-1]["Close"])
        end_price = float(hist.iloc[-1]["Close"])

        if start_price == 0:
            return None

        return round((end_price - start_price) / start_price * 100, 2)
