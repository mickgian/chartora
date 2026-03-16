import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from backend/ directory (if it exists)
_backend_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(_backend_dir / ".env")


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


@dataclass
class Settings:
    """Application settings."""

    app_name: str = "Chartora"
    debug: bool = False

    # Database
    database_url: str = field(
        default_factory=lambda: _env(
            "CHARTORA_DATABASE_URL",
            "postgresql+asyncpg://chartora:chartora@localhost:5432/chartora",
        )
    )

    # External APIs
    news_api_key: str = field(default_factory=lambda: _env("CHARTORA_NEWS_API_KEY"))
    claude_api_key: str = field(default_factory=lambda: _env("CHARTORA_CLAUDE_API_KEY"))
    uspto_api_key: str = field(
        default_factory=lambda: _env("CHARTORA_USPTO_API_KEY")
    )
    sec_edgar_user_agent: str = field(
        default_factory=lambda: _env(
            "SEC_EDGAR_USER_AGENT", "Chartora contact@chartora.io"
        )
    )

    # Stripe
    stripe_secret_key: str = field(default_factory=lambda: _env("STRIPE_SECRET_KEY"))
    stripe_webhook_secret: str = field(
        default_factory=lambda: _env("STRIPE_WEBHOOK_SECRET")
    )
    stripe_price_id: str = field(default_factory=lambda: _env("STRIPE_PRICE_ID"))
    frontend_url: str = field(
        default_factory=lambda: _env("CHARTORA_FRONTEND_URL", "http://localhost:3000")
    )

    # Auth / JWT
    jwt_secret_key: str = field(
        default_factory=lambda: _env(
            "CHARTORA_JWT_SECRET_KEY", "change-me-in-production"
        )
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # Email (Resend.com)
    resend_api_key: str = field(default_factory=lambda: _env("RESEND_API_KEY"))
    email_from: str = "noreply@chartora.com"

    # Data refresh
    force_refresh: bool = field(
        default_factory=lambda: _env("CHARTORA_FORCE_REFRESH", "false").lower()
        in ("true", "1", "yes")
    )

    # Cache
    cache_ttl_seconds: int = 300

    # Server
    host: str = field(default="0.0.0.0")
    port: int = 8000
