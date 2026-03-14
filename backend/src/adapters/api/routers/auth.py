"""Authentication routes for user registration, login, and password reset."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import jwt as pyjwt
from fastapi import APIRouter, HTTPException, Request

from src.adapters.api.dependencies import UserRepoDep, get_settings
from src.infrastructure.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_password_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from src.infrastructure.email_service import send_password_reset_email

if TYPE_CHECKING:
    from src.domain.models.entities import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# In-memory store for password reset tokens (maps hashed_token → email).
# In production, this would be in Redis or DB with TTL.
_reset_tokens: dict[str, str] = {}


@router.post("/register")
async def register(
    request: Request,
    user_repo: UserRepoDep,
) -> dict[str, Any]:
    """Register a new user with email and password."""
    body = await request.json()
    email: str | None = body.get("email")
    password: str | None = body.get("password")

    if not email or "@" not in email:
        raise HTTPException(status_code=422, detail="A valid email is required")
    if not password or len(password) < 8:
        raise HTTPException(
            status_code=422, detail="Password must be at least 8 characters"
        )

    existing = await user_repo.get_by_email(email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    from src.domain.models.entities import User

    user = User(email=email, password_hash=hash_password(password))
    saved = await user_repo.save(user)

    settings = get_settings(request)
    access_token = create_access_token(saved.id, saved.email, settings)  # type: ignore[arg-type]
    refresh_token = create_refresh_token(saved.id, settings)  # type: ignore[arg-type]

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": saved.id,
            "email": saved.email,
            "is_premium": saved.is_premium,
        },
    }


@router.post("/login")
async def login(
    request: Request,
    user_repo: UserRepoDep,
) -> dict[str, Any]:
    """Authenticate with email and password."""
    body = await request.json()
    email: str | None = body.get("email")
    password: str | None = body.get("password")

    if not email or not password:
        raise HTTPException(status_code=422, detail="Email and password are required")

    user = await user_repo.get_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    settings = get_settings(request)
    access_token = create_access_token(user.id, user.email, settings)  # type: ignore[arg-type]
    refresh_token = create_refresh_token(user.id, settings)  # type: ignore[arg-type]

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "is_premium": user.is_premium,
        },
    }


@router.get("/me")
async def get_current_user(
    request: Request,
    user_repo: UserRepoDep,
) -> dict[str, Any]:
    """Get current authenticated user profile."""
    user = await _get_user_from_token(request, user_repo)
    return {
        "id": user.id,
        "email": user.email,
        "is_premium": user.is_premium,
        "subscription_status": user.subscription_status.value,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/refresh")
async def refresh_token(
    request: Request,
    user_repo: UserRepoDep,
) -> dict[str, Any]:
    """Refresh an access token using a refresh token."""
    body = await request.json()
    token: str | None = body.get("refresh_token")
    if not token:
        raise HTTPException(status_code=422, detail="Refresh token is required")

    settings = get_settings(request)
    try:
        payload = decode_token(token, settings)
    except pyjwt.PyJWTError as exc:
        raise HTTPException(
            status_code=401, detail="Invalid or expired refresh token"
        ) from exc

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = int(payload["sub"])
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(user.id, user.email, settings)  # type: ignore[arg-type]

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/password-reset")
async def request_password_reset(
    request: Request,
    user_repo: UserRepoDep,
) -> dict[str, str]:
    """Request a password reset email."""
    body = await request.json()
    email: str | None = body.get("email")
    if not email:
        raise HTTPException(status_code=422, detail="Email is required")

    # Always return success to prevent email enumeration
    user = await user_repo.get_by_email(email)
    if user is not None:
        settings = get_settings(request)
        token = generate_password_reset_token()
        _reset_tokens[hash_reset_token(token)] = email
        await send_password_reset_email(email, token, settings)

    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: Request,
    user_repo: UserRepoDep,
) -> dict[str, str]:
    """Reset password using a valid reset token."""
    body = await request.json()
    token: str | None = body.get("token")
    new_password: str | None = body.get("new_password")

    if not token or not new_password:
        raise HTTPException(
            status_code=422, detail="Token and new_password are required"
        )
    if len(new_password) < 8:
        raise HTTPException(
            status_code=422, detail="Password must be at least 8 characters"
        )

    hashed_token = hash_reset_token(token)
    email = _reset_tokens.pop(hashed_token, None)
    if email is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = await user_repo.get_by_email(email)
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")

    user.password_hash = hash_password(new_password)
    await user_repo.update(user)

    return {"message": "Password has been reset successfully."}


async def _get_user_from_token(
    request: Request,
    user_repo: UserRepoDep,
) -> Any:
    """Extract and validate user from Authorization header."""

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header[7:]
    settings = get_settings(request)
    try:
        payload = decode_token(token, settings)
    except pyjwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = int(payload["sub"])
    user: User | None = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
