"""Add unique constraint on (company_id, url) to news_articles.

Deduplicates existing rows before adding the constraint.

Revision ID: 004
Revises: 003
Create Date: 2026-03-18
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Delete duplicate rows, keeping the one with the lowest id per (company_id, url)
    op.execute(
        """
        DELETE FROM news_articles
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM news_articles
            GROUP BY company_id, url
        )
        """
    )
    op.create_unique_constraint(
        "uq_news_company_url", "news_articles", ["company_id", "url"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_news_company_url", "news_articles", type_="unique")
