"""Pydantic response schemas for the API."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    sector: str
    ticker: str | None
    description: str | None
    is_etf: bool
    website: str | None
    logo_url: str | None


class ScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_score: float
    stock_momentum: float
    patent_velocity: float
    qubit_progress: float
    funding_strength: float
    news_sentiment: float
    score_date: date
    rank: int | None
    rank_change: int | None


class LeaderboardEntry(BaseModel):
    rank: int
    company: CompanyResponse
    score: ScoreResponse
    trend: str
    metric_value: float


class LeaderboardResponse(BaseModel):
    metric: str
    entries: list[LeaderboardEntry]
    count: int
    updated_at: datetime | None


class StockPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    price_date: date
    close_price: float
    open_price: float | None
    high_price: float | None
    low_price: float | None
    volume: int | None
    market_cap: int | None


class PatentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patent_number: str
    title: str
    filing_date: date
    source: str
    abstract: str | None
    grant_date: date | None
    classification: str | None


class NewsArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    url: str
    published_at: datetime
    source_name: str | None
    sentiment: str | None
    sentiment_score: float | None


class FilingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filing_type: str
    filing_date: date
    description: str | None
    url: str | None


class CompanyDetailResponse(BaseModel):
    company: CompanyResponse
    score: ScoreResponse | None


class StockHistoryResponse(BaseModel):
    company_slug: str
    prices: list[StockPriceResponse]
    count: int


class PatentListResponse(BaseModel):
    company_slug: str
    patents: list[PatentResponse]
    count: int


class NewsListResponse(BaseModel):
    company_slug: str
    articles: list[NewsArticleResponse]
    count: int


class FilingListResponse(BaseModel):
    company_slug: str
    filings: list[FilingResponse]
    count: int


class RankingEntry(BaseModel):
    rank: int
    company: CompanyResponse
    metric_value: float
    trend: str


class RankingResponse(BaseModel):
    metric: str
    entries: list[RankingEntry]
    count: int


class ErrorResponse(BaseModel):
    detail: str
