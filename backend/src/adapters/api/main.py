from typing import Any

from fastapi import FastAPI

from src.config.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title=settings.app_name,
        description="Quantum Computing Company Leaderboard API",
        version="0.1.0",
    )

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        return {"status": "healthy"}

    return app


app = create_app()
