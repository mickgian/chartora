"""Unit tests verifying interface contracts for repository and data source ports."""

import inspect

import pytest

from src.domain.interfaces import (
    CompanyRepository,
    FilingDataSource,
    FilingRepository,
    NewsDataSource,
    NewsRepository,
    PatentDataSource,
    PatentRepository,
    ScoreRepository,
    SentimentAnalyzer,
    StockDataSource,
    StockRepository,
)

# ─── Repository interface contracts ────────────────────────────────────────────


class TestCompanyRepositoryContract:
    def test_has_get_by_id(self) -> None:
        assert hasattr(CompanyRepository, "get_by_id")
        sig = inspect.signature(CompanyRepository.get_by_id)
        assert "company_id" in sig.parameters

    def test_has_get_by_slug(self) -> None:
        assert hasattr(CompanyRepository, "get_by_slug")
        sig = inspect.signature(CompanyRepository.get_by_slug)
        assert "slug" in sig.parameters

    def test_has_get_all(self) -> None:
        assert hasattr(CompanyRepository, "get_all")

    def test_has_save(self) -> None:
        assert hasattr(CompanyRepository, "save")

    def test_has_delete(self) -> None:
        assert hasattr(CompanyRepository, "delete")

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            CompanyRepository()  # type: ignore[abstract]


class TestStockRepositoryContract:
    def test_has_get_latest(self) -> None:
        sig = inspect.signature(StockRepository.get_latest)
        assert "company_id" in sig.parameters

    def test_has_get_by_date_range(self) -> None:
        sig = inspect.signature(StockRepository.get_by_date_range)
        assert "company_id" in sig.parameters
        assert "date_range" in sig.parameters

    def test_has_save(self) -> None:
        assert hasattr(StockRepository, "save")

    def test_has_save_many(self) -> None:
        assert hasattr(StockRepository, "save_many")

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            StockRepository()  # type: ignore[abstract]


class TestPatentRepositoryContract:
    def test_has_get_by_company(self) -> None:
        sig = inspect.signature(PatentRepository.get_by_company)
        assert "company_id" in sig.parameters

    def test_has_count_by_date_range(self) -> None:
        sig = inspect.signature(PatentRepository.count_by_date_range)
        assert "company_id" in sig.parameters
        assert "date_range" in sig.parameters

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            PatentRepository()  # type: ignore[abstract]


class TestScoreRepositoryContract:
    def test_has_get_latest(self) -> None:
        sig = inspect.signature(ScoreRepository.get_latest)
        assert "company_id" in sig.parameters

    def test_has_get_latest_all(self) -> None:
        assert hasattr(ScoreRepository, "get_latest_all")

    def test_has_save(self) -> None:
        assert hasattr(ScoreRepository, "save")

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            ScoreRepository()  # type: ignore[abstract]


class TestNewsRepositoryContract:
    def test_has_get_by_company(self) -> None:
        sig = inspect.signature(NewsRepository.get_by_company)
        assert "company_id" in sig.parameters
        assert "limit" in sig.parameters

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            NewsRepository()  # type: ignore[abstract]


class TestFilingRepositoryContract:
    def test_has_get_by_company(self) -> None:
        sig = inspect.signature(FilingRepository.get_by_company)
        assert "company_id" in sig.parameters

    def test_has_get_by_type(self) -> None:
        sig = inspect.signature(FilingRepository.get_by_type)
        assert "filing_type" in sig.parameters

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            FilingRepository()  # type: ignore[abstract]


# ─── Data source interface contracts ───────────────────────────────────────────


class TestStockDataSourceContract:
    def test_has_fetch_current_price(self) -> None:
        sig = inspect.signature(StockDataSource.fetch_current_price)
        assert "ticker" in sig.parameters

    def test_has_fetch_history(self) -> None:
        sig = inspect.signature(StockDataSource.fetch_history)
        assert "ticker" in sig.parameters
        assert "date_range" in sig.parameters

    def test_has_fetch_performance(self) -> None:
        sig = inspect.signature(StockDataSource.fetch_performance)
        assert "days" in sig.parameters

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            StockDataSource()  # type: ignore[abstract]


class TestPatentDataSourceContract:
    def test_has_search_patents(self) -> None:
        sig = inspect.signature(PatentDataSource.search_patents)
        assert "company_name" in sig.parameters

    def test_has_get_patent_count(self) -> None:
        sig = inspect.signature(PatentDataSource.get_patent_count)
        assert "company_name" in sig.parameters

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            PatentDataSource()  # type: ignore[abstract]


class TestNewsDataSourceContract:
    def test_has_fetch_articles(self) -> None:
        sig = inspect.signature(NewsDataSource.fetch_articles)
        assert "company_name" in sig.parameters

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            NewsDataSource()  # type: ignore[abstract]


class TestFilingDataSourceContract:
    def test_has_fetch_filings(self) -> None:
        sig = inspect.signature(FilingDataSource.fetch_filings)
        assert "ticker" in sig.parameters

    def test_has_fetch_insider_trades(self) -> None:
        assert hasattr(FilingDataSource, "fetch_insider_trades")

    def test_has_fetch_institutional_holdings(self) -> None:
        assert hasattr(FilingDataSource, "fetch_institutional_holdings")

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            FilingDataSource()  # type: ignore[abstract]


class TestSentimentAnalyzerContract:
    def test_has_analyze(self) -> None:
        sig = inspect.signature(SentimentAnalyzer.analyze)
        assert "text" in sig.parameters

    def test_has_analyze_batch(self) -> None:
        sig = inspect.signature(SentimentAnalyzer.analyze_batch)
        assert "texts" in sig.parameters

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            SentimentAnalyzer()  # type: ignore[abstract]
