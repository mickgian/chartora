"""Add government_contracts table.

Revision ID: 003
Revises: 002
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "government_contracts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("award_id", sa.String(100), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(16, 2), nullable=False),
        sa.Column("awarding_agency", sa.String(500), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id", "award_id", name="uq_contract_company_award"
        ),
    )


def downgrade() -> None:
    op.drop_table("government_contracts")
