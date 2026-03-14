"""PostgreSQL implementation of the ApiKeyRepository interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from src.domain.interfaces.repositories import ApiKeyRepository
from src.domain.models.entities import ApiKey
from src.infrastructure.database import ApiKeyTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PgApiKeyRepository(ApiKeyRepository):
    """PostgreSQL-backed API key repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_key_hash(self, key_hash: str) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKeyTable).where(ApiKeyTable.key_hash == key_hash)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_user(self, user_id: int) -> list[ApiKey]:
        result = await self._session.execute(
            select(ApiKeyTable)
            .where(ApiKeyTable.user_id == user_id)
            .order_by(ApiKeyTable.created_at.desc())
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def save(self, api_key: ApiKey) -> ApiKey:
        row = ApiKeyTable(
            user_id=api_key.user_id,
            key_hash=api_key.key_hash,
            name=api_key.name,
            prefix=api_key.prefix,
            is_active=api_key.is_active,
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    async def update(self, api_key: ApiKey) -> ApiKey:
        result = await self._session.execute(
            select(ApiKeyTable).where(ApiKeyTable.id == api_key.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"API key with id {api_key.id} not found")
        row.is_active = api_key.is_active
        row.last_used_at = api_key.last_used_at
        await self._session.flush()
        return self._to_entity(row)

    async def delete(self, key_id: int) -> None:
        await self._session.execute(
            delete(ApiKeyTable).where(ApiKeyTable.id == key_id)
        )
        await self._session.flush()

    @staticmethod
    def _to_entity(row: ApiKeyTable) -> ApiKey:
        return ApiKey(
            id=row.id,
            user_id=row.user_id,
            key_hash=row.key_hash,
            name=row.name,
            prefix=row.prefix,
            created_at=row.created_at,
            last_used_at=row.last_used_at,
            is_active=row.is_active,
        )
