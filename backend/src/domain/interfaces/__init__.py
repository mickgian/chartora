"""Domain interfaces (ports) for Chartora."""

from src.domain.interfaces.data_sources import (
    FilingDataSource,
    NewsDataSource,
    PatentDataSource,
    SentimentAnalyzer,
    StockDataSource,
)
from src.domain.interfaces.repositories import (
    CompanyRepository,
    FilingRepository,
    NewsRepository,
    PatentRepository,
    ScoreRepository,
    StockRepository,
)

__all__ = [
    "CompanyRepository",
    "FilingDataSource",
    "FilingRepository",
    "NewsDataSource",
    "NewsRepository",
    "PatentDataSource",
    "PatentRepository",
    "ScoreRepository",
    "SentimentAnalyzer",
    "StockDataSource",
    "StockRepository",
]
