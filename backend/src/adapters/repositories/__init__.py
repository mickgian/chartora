"""PostgreSQL repository implementations."""

from src.adapters.repositories.alert_preference_repository import (
    PgAlertPreferenceRepository,
)
from src.adapters.repositories.api_key_repository import PgApiKeyRepository
from src.adapters.repositories.company_repository import PgCompanyRepository
from src.adapters.repositories.filing_repository import PgFilingRepository
from src.adapters.repositories.government_contract_repository import (
    PgGovernmentContractRepository,
)
from src.adapters.repositories.news_repository import PgNewsRepository
from src.adapters.repositories.patent_repository import PgPatentRepository
from src.adapters.repositories.score_repository import PgScoreRepository
from src.adapters.repositories.stock_repository import PgStockRepository
from src.adapters.repositories.user_repository import PgUserRepository

__all__ = [
    "PgAlertPreferenceRepository",
    "PgApiKeyRepository",
    "PgCompanyRepository",
    "PgFilingRepository",
    "PgGovernmentContractRepository",
    "PgNewsRepository",
    "PgPatentRepository",
    "PgScoreRepository",
    "PgStockRepository",
    "PgUserRepository",
]
