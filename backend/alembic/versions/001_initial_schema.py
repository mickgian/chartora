"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-03-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("ticker", sa.String(10), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sector", sa.String(50), nullable=False, server_default="pure_play"),
        sa.Column("is_etf", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        sa.UniqueConstraint("ticker"),
    )

    op.create_table(
        "stock_prices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("open_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("high_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("low_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("close_price", sa.Numeric(12, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("market_cap", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("company_id", "price_date", name="uq_stock_company_date"),
    )

    op.create_table(
        "patents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("patent_number", sa.String(50), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("filing_date", sa.Date(), nullable=False),
        sa.Column("grant_date", sa.Date(), nullable=True),
        sa.Column("source", sa.String(10), nullable=False, server_default="USPTO"),
        sa.Column("classification", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "patent_number", "source", name="uq_patent_number_source"
        ),
    )

    op.create_table(
        "scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("score_date", sa.Date(), nullable=False),
        sa.Column("total_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("stock_momentum", sa.Numeric(5, 2), nullable=False),
        sa.Column("patent_velocity", sa.Numeric(5, 2), nullable=False),
        sa.Column("qubit_progress", sa.Numeric(5, 2), nullable=False),
        sa.Column("funding_strength", sa.Numeric(5, 2), nullable=False),
        sa.Column("news_sentiment", sa.Numeric(5, 2), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("rank_change", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "company_id", "score_date", name="uq_score_company_date"
        ),
    )

    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("source_name", sa.String(255), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("sentiment", sa.String(10), nullable=True),
        sa.Column("sentiment_score", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="CASCADE"
        ),
    )

    op.create_table(
        "filings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("filing_type", sa.String(20), nullable=False),
        sa.Column("filing_date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(1000), nullable=True),
        sa.Column("data_json", sa.Text(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for common queries
    op.create_index("ix_stock_prices_price_date", "stock_prices", ["price_date"])
    op.create_index("ix_patents_filing_date", "patents", ["filing_date"])
    op.create_index("ix_scores_score_date", "scores", ["score_date"])
    op.create_index("ix_news_articles_published_at", "news_articles", ["published_at"])
    op.create_index("ix_filings_filing_date", "filings", ["filing_date"])


def downgrade() -> None:
    op.drop_table("filings")
    op.drop_table("news_articles")
    op.drop_table("scores")
    op.drop_table("patents")
    op.drop_table("stock_prices")
    op.drop_table("companies")
