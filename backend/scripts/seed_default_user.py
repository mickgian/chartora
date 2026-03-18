"""Seed script to create a default test user with premium access.

Creates a user that can be used for local development and testing:
  Email:    demo@chartora.com
  Password: chartora123

The user is created with an active subscription so premium features
are immediately available without Stripe configuration.
"""

import os
import sys
from pathlib import Path

import bcrypt
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env from backend/ directory
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEFAULT_EMAIL = "demo@chartora.com"
DEFAULT_PASSWORD = "chartora123"


def _hash_password(password: str) -> str:
    raw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return raw.decode("utf-8")


def seed(database_url: str | None = None) -> None:
    """Insert a default premium user into the database."""
    url = database_url or os.environ.get(
        "CHARTORA_DATABASE_URL",
        "postgresql://chartora:chartora@localhost:5432/chartora",
    )
    # Strip async driver — this script uses synchronous SQLAlchemy
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(url)

    password_hash = _hash_password(DEFAULT_PASSWORD)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO users (email, password_hash, subscription_status)
                VALUES (:email, :password_hash, :subscription_status)
                ON CONFLICT (email) DO UPDATE
                    SET subscription_status = :subscription_status
                """
            ),
            {
                "email": DEFAULT_EMAIL,
                "password_hash": password_hash,
                "subscription_status": "active",
            },
        )
    print(
        f"Default user created: {DEFAULT_EMAIL}"
        f" / {DEFAULT_PASSWORD} (premium: active)"
    )


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else None
    seed(url)
