from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CompanyTable(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(10), unique=True, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sector: Mapped[str] = mapped_column(String(50), nullable=False, default="pure_play")
    is_etf: Mapped[bool] = mapped_column(Boolean, default=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    stock_prices: Mapped[list["StockPriceTable"]] = relationship(
        back_populates="company"
    )
    patents: Mapped[list["PatentTable"]] = relationship(back_populates="company")
    scores: Mapped[list["ScoreTable"]] = relationship(back_populates="company")
    news_articles: Mapped[list["NewsArticleTable"]] = relationship(
        back_populates="company"
    )
    filings: Mapped[list["FilingTable"]] = relationship(back_populates="company")


class StockPriceTable(Base):
    __tablename__ = "stock_prices"
    __table_args__ = (
        UniqueConstraint("company_id", "price_date", name="uq_stock_company_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    high_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    low_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    close_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    market_cap: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    company: Mapped["CompanyTable"] = relationship(back_populates="stock_prices")


class PatentTable(Base):
    __tablename__ = "patents"
    __table_args__ = (
        UniqueConstraint("patent_number", "source", name="uq_patent_number_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    patent_number: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    filing_date: Mapped[date] = mapped_column(Date, nullable=False)
    grant_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(
        String(10), nullable=False, default="USPTO"
    )  # USPTO or EPO
    classification: Mapped[str | None] = mapped_column(String(50), nullable=True)

    company: Mapped["CompanyTable"] = relationship(back_populates="patents")


class ScoreTable(Base):
    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint("company_id", "score_date", name="uq_score_company_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    score_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    stock_momentum: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    patent_velocity: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    qubit_progress: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    funding_strength: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    news_sentiment: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_change: Mapped[int | None] = mapped_column(Integer, nullable=True)

    company: Mapped["CompanyTable"] = relationship(back_populates="scores")


class NewsArticleTable(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sentiment: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # bullish, bearish, neutral
    sentiment_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    company: Mapped["CompanyTable"] = relationship(back_populates="news_articles")


class FilingTable(Base):
    __tablename__ = "filings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    filing_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 10-K, 10-Q, Form4, 13F
    filing_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    data_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    company: Mapped["CompanyTable"] = relationship(back_populates="filings")
