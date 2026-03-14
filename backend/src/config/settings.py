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

    # Server
    host: str = field(default="0.0.0.0")
    port: int = 8000
