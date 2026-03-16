"""Dependency injection for FastAPI routes.

Provides repository and data source instances via FastAPI's Depends system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.adapters.repositories import (
    PgAlertPreferenceRepository,
    PgApiKeyRepository,
    PgCompanyRepository,
    PgFilingRepository,
    PgGovernmentContractRepository,
    PgNewsRepository,
    PgPatentRepository,
    PgScoreRepository,
    PgStockRepository,
    PgUserRepository,
)
from src.domain.interfaces.repositories import (
    AlertPreferenceRepository,
    ApiKeyRepository,
    CompanyRepository,
    FilingRepository,
    GovernmentContractRepository,
    NewsRepository,
    PatentRepository,
    ScoreRepository,
    StockRepository,
    UserRepository,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from src.config.settings import Settings

# Module-level engine and session factory, initialized lazily
_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(
    settings: Settings,
) -> async_sessionmaker[AsyncSession]:
    """Initialize the database engine and session factory."""
    global _engine, _session_factory
    _engine = create_async_engine(settings.database_url, echo=settings.debug)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _session_factory


def get_settings(request: Request) -> Settings:
    """Retrieve the Settings instance stored on the app."""
    settings: Settings = request.app.state.settings
    return settings


async def get_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session per request."""
    factory: async_sessionmaker[AsyncSession] | None = getattr(
        request.app.state, "session_factory", None
    )
    if factory is None:
        settings = get_settings(request)
        factory = init_db(settings)
        request.app.state.session_factory = factory

    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# These Annotated types are used at runtime by FastAPI's DI,
# so they MUST remain as runtime imports.
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_company_repo(
    session: SessionDep,
) -> CompanyRepository:
    return PgCompanyRepository(session)


def get_stock_repo(
    session: SessionDep,
) -> StockRepository:
    return PgStockRepository(session)


def get_patent_repo(
    session: SessionDep,
) -> PatentRepository:
    return PgPatentRepository(session)


def get_score_repo(
    session: SessionDep,
) -> ScoreRepository:
    return PgScoreRepository(session)


def get_news_repo(
    session: SessionDep,
) -> NewsRepository:
    return PgNewsRepository(session)


def get_filing_repo(
    session: SessionDep,
) -> FilingRepository:
    return PgFilingRepository(session)


def get_user_repo(
    session: SessionDep,
) -> UserRepository:
    return PgUserRepository(session)


def get_alert_pref_repo(
    session: SessionDep,
) -> AlertPreferenceRepository:
    return PgAlertPreferenceRepository(session)


def get_api_key_repo(
    session: SessionDep,
) -> ApiKeyRepository:
    return PgApiKeyRepository(session)


def get_gov_contract_repo(
    session: SessionDep,
) -> GovernmentContractRepository:
    return PgGovernmentContractRepository(session)


CompanyRepoDep = Annotated[CompanyRepository, Depends(get_company_repo)]
StockRepoDep = Annotated[StockRepository, Depends(get_stock_repo)]
PatentRepoDep = Annotated[PatentRepository, Depends(get_patent_repo)]
ScoreRepoDep = Annotated[ScoreRepository, Depends(get_score_repo)]
NewsRepoDep = Annotated[NewsRepository, Depends(get_news_repo)]
FilingRepoDep = Annotated[FilingRepository, Depends(get_filing_repo)]
UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]
AlertPrefRepoDep = Annotated[AlertPreferenceRepository, Depends(get_alert_pref_repo)]
ApiKeyRepoDep = Annotated[ApiKeyRepository, Depends(get_api_key_repo)]
GovContractRepoDep = Annotated[
    GovernmentContractRepository, Depends(get_gov_contract_repo)
]
