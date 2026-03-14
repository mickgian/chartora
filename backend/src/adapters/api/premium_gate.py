"""Premium gate middleware for protecting premium-only endpoints."""

from __future__ import annotations

import hashlib
from datetime import UTC
from typing import Any

import jwt as pyjwt
from fastapi import HTTPException, Request

from src.adapters.api.dependencies import get_settings
from src.infrastructure.auth import decode_token


async def require_premium(request: Request) -> dict[str, Any]:
    """FastAPI dependency that gates access to premium-only endpoints.

    Validates JWT token and checks for an active premium subscription.
    Also supports API key authentication for programmatic access.
    """
    auth_header = request.headers.get("Authorization", "")

    # Try Bearer token (JWT) first
    if auth_header.startswith("Bearer "):
        return await _validate_jwt(request, auth_header[7:])

    # Try API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return await _validate_api_key(request, api_key)

    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide a Bearer token or X-API-Key.",
    )


async def _validate_jwt(request: Request, token: str) -> dict[str, Any]:
    """Validate JWT and check premium subscription."""
    settings = get_settings(request)
    try:
        payload = decode_token(token, settings)
    except pyjwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = int(payload["sub"])

    # Check subscription status from DB

    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="Service unavailable")

    async with factory() as session:
        from src.adapters.repositories import PgUserRepository

        repo = PgUserRepository(session)
        user = await repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.is_premium:
            raise HTTPException(
                status_code=403,
                detail="Premium subscription required. Subscribe at /pro.",
            )

        return {"premium": True, "user_id": user_id, "email": user.email}


async def _validate_api_key(request: Request, api_key: str) -> dict[str, Any]:
    """Validate API key and check premium subscription."""
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="Service unavailable")

    async with factory() as session:
        from src.adapters.repositories import PgApiKeyRepository, PgUserRepository

        key_repo = PgApiKeyRepository(session)
        api_key_entity = await key_repo.get_by_key_hash(key_hash)
        if api_key_entity is None or not api_key_entity.is_active:
            raise HTTPException(status_code=401, detail="Invalid API key")

        user_repo = PgUserRepository(session)
        user = await user_repo.get_by_id(api_key_entity.user_id)
        if user is None or not user.is_premium:
            raise HTTPException(
                status_code=403,
                detail="Premium subscription required.",
            )

        # Update last_used_at
        from datetime import datetime

        api_key_entity.last_used_at = datetime.now(UTC)
        await key_repo.update(api_key_entity)
        await session.commit()

        return {
            "premium": True,
            "user_id": user.id,
            "email": user.email,
        }
