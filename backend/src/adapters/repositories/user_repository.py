"""PostgreSQL implementation of the UserRepository interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, select

from src.domain.interfaces.repositories import UserRepository
from src.domain.models.entities import User
from src.domain.models.value_objects import SubscriptionStatus
from src.infrastructure.database import UserTable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PgUserRepository(UserRepository):
    """PostgreSQL-backed user repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(UserTable).where(UserTable.id == user_id)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserTable).where(UserTable.email == email)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_stripe_customer_id(self, customer_id: str) -> User | None:
        result = await self._session.execute(
            select(UserTable).where(UserTable.stripe_customer_id == customer_id)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_stripe_subscription_id(self, subscription_id: str) -> User | None:
        result = await self._session.execute(
            select(UserTable).where(
                UserTable.stripe_subscription_id == subscription_id
            )
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def save(self, user: User) -> User:
        row = UserTable(
            email=user.email,
            password_hash=user.password_hash,
            subscription_status=user.subscription_status.value,
            stripe_customer_id=user.stripe_customer_id,
            stripe_subscription_id=user.stripe_subscription_id,
        )
        self._session.add(row)
        await self._session.flush()
        return self._to_entity(row)

    async def update(self, user: User) -> User:
        result = await self._session.execute(
            select(UserTable).where(UserTable.id == user.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"User with id {user.id} not found")
        row.email = user.email
        row.password_hash = user.password_hash
        row.subscription_status = user.subscription_status.value
        row.stripe_customer_id = user.stripe_customer_id
        row.stripe_subscription_id = user.stripe_subscription_id
        await self._session.flush()
        return self._to_entity(row)

    async def delete(self, user_id: int) -> None:
        await self._session.execute(
            delete(UserTable).where(UserTable.id == user_id)
        )
        await self._session.flush()

    @staticmethod
    def _to_entity(row: UserTable) -> User:
        return User(
            id=row.id,
            email=row.email,
            password_hash=row.password_hash,
            subscription_status=SubscriptionStatus(row.subscription_status),
            stripe_customer_id=row.stripe_customer_id,
            stripe_subscription_id=row.stripe_subscription_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
