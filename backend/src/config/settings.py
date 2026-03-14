from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application settings."""

    app_name: str = "Chartora"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://chartora:chartora@localhost:5432/chartora"

    # External APIs
    news_api_key: str = ""
    claude_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""
    frontend_url: str = "http://localhost:3000"

    # Auth / JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # Email (Resend.com)
    resend_api_key: str = ""
    email_from: str = "noreply@chartora.com"

    # Server
    host: str = field(default="0.0.0.0")
    port: int = 8000
