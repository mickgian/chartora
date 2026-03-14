"""Tests for database schema definitions."""

from src.infrastructure.database import (
    Base,
    CompanyTable,
    FilingTable,
    NewsArticleTable,
    PatentTable,
    ScoreTable,
    StockPriceTable,
)


def test_all_tables_registered():
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "companies",
        "stock_prices",
        "patents",
        "scores",
        "news_articles",
        "filings",
        "users",
        "alert_preferences",
        "api_keys",
    }
    assert expected == table_names


def test_companies_table_columns():
    columns = {c.name for c in CompanyTable.__table__.columns}
    assert "id" in columns
    assert "name" in columns
    assert "slug" in columns
    assert "ticker" in columns
    assert "sector" in columns
    assert "is_etf" in columns


def test_stock_prices_table_has_unique_constraint():
    constraints = StockPriceTable.__table__.constraints
    unique_names = {
        c.name for c in constraints if hasattr(c, "name") and c.name is not None
    }
    assert "uq_stock_company_date" in unique_names


def test_scores_table_columns():
    columns = {c.name for c in ScoreTable.__table__.columns}
    expected_score_components = {
        "total_score",
        "stock_momentum",
        "patent_velocity",
        "qubit_progress",
        "funding_strength",
        "news_sentiment",
    }
    assert expected_score_components.issubset(columns)


def test_patents_table_has_source():
    columns = {c.name for c in PatentTable.__table__.columns}
    assert "source" in columns
    assert "patent_number" in columns


def test_news_articles_table_has_sentiment():
    columns = {c.name for c in NewsArticleTable.__table__.columns}
    assert "sentiment" in columns
    assert "sentiment_score" in columns


def test_filings_table_columns():
    columns = {c.name for c in FilingTable.__table__.columns}
    assert "filing_type" in columns
    assert "filing_date" in columns
    assert "data_json" in columns
