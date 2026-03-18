"""Remove irrelevant news articles for all companies.

Deletes articles whose titles don't contain any quantum keyword AND
don't contain the company name.  This cleans up ETF roundup / financial
news that was ingested before the relevance filter was added.

Revision ID: 005
Revises: 004
Create Date: 2026-03-18
"""

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

# Quantum keywords that make an article relevant regardless of company
_QUANTUM_KEYWORDS = (
    "quantum",
    "qubit",
    "superconducting",
    "trapped-ion",
    "annealing",
    "error correction",
    "topological",
    "cryogenic",
    "entanglement",
    "superposition",
)


def upgrade() -> None:
    # Build a SQL condition that keeps articles matching any quantum keyword
    # OR articles whose title contains the company name.
    quantum_conditions = " OR ".join(
        f"LOWER(na.title) LIKE '%{kw}%'" for kw in _QUANTUM_KEYWORDS
    )

    op.execute(
        f"""
        DELETE FROM news_articles na
        USING companies c
        WHERE na.company_id = c.id
          AND NOT ({quantum_conditions})
          AND LOWER(na.title) NOT LIKE '%' || LOWER(c.name) || '%'
          AND LOWER(na.title) NOT LIKE '%' || LOWER(SPLIT_PART(c.name, ' ', 1)) || '%'
        """
    )


def downgrade() -> None:
    # Data deletion is not reversible
    pass
