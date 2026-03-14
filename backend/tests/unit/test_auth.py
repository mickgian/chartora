"""Tests for authentication infrastructure and routes."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.adapters.api.main import create_app
from src.config.settings import Settings
from src.domain.models.entities import User
from src.infrastructure.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    generate_password_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)


# ── Password hashing tests ──


def test_hash_and_verify_password():
    hashed = hash_password("mysecurepassword")
    assert hashed != "mysecurepassword"
    assert verify_password("mysecurepassword", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


# ── JWT token tests ──


@pytest.fixture
def settings():
    return Settings(
        database_url="sqlite+aiosqlite:///test.db",
        jwt_secret_key="test-secret-key-for-testing-32ch",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=60,
        jwt_refresh_token_expire_days=30,
    )


def test_create_and_decode_access_token(settings):
    token = create_access_token(1, "user@example.com", settings)
    payload = decode_token(token, settings)
    assert payload["sub"] == "1"
    assert payload["email"] == "user@example.com"
    assert payload["type"] == "access"


def test_create_and_decode_refresh_token(settings):
    token = create_refresh_token(1, settings)
    payload = decode_token(token, settings)
    assert payload["sub"] == "1"
    assert payload["type"] == "refresh"


def test_expired_token_raises(settings):
    import jwt as pyjwt

    token = create_access_token(
        1, "user@example.com", settings, expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_token(token, settings)


def test_invalid_token_raises(settings):
    import jwt as pyjwt

    with pytest.raises(pyjwt.DecodeError):
        decode_token("not.a.valid.token", settings)


# ── Password reset token tests ──


def test_generate_and_hash_reset_token():
    token = generate_password_reset_token()
    assert len(token) > 20
    hashed = hash_reset_token(token)
    assert hashed != token
    # Same input produces same hash
    assert hash_reset_token(token) == hashed


# ── API key generation tests ──


def test_generate_api_key():
    full_key, key_hash, prefix = generate_api_key()
    assert full_key.startswith("ck_")
    assert len(key_hash) == 64  # SHA-256 hex
    assert prefix == full_key[:10]


# ── Auth route tests ──


@pytest.fixture
def auth_client():
    import asyncio

    from sqlalchemy.ext.asyncio import (
        async_sessionmaker,
        create_async_engine,
    )

    from src.infrastructure.database import Base

    test_settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        jwt_secret_key="test-jwt-secret-key-32-chars-ok!",
        stripe_secret_key="sk_test_fake",
        stripe_webhook_secret="whsec_fake",
    )
    app = create_app(test_settings)

    # Create tables in-memory
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
        _create_tables()
    )
    app.state.session_factory = factory

    return TestClient(app)


def test_register_requires_valid_email(auth_client):
    response = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "invalid", "password": "password123"},
    )
    assert response.status_code == 422
    assert "valid email" in response.json()["detail"]


def test_register_requires_password_length(auth_client):
    response = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "short"},
    )
    assert response.status_code == 422
    assert "8 characters" in response.json()["detail"]


def test_login_requires_email_and_password(auth_client):
    response = auth_client.post(
        "/api/v1/auth/login",
        json={},
    )
    assert response.status_code == 422


def test_me_requires_auth(auth_client):
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_rejects_invalid_token(auth_client):
    response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


def test_refresh_requires_token(auth_client):
    response = auth_client.post(
        "/api/v1/auth/refresh",
        json={},
    )
    assert response.status_code == 422


def test_password_reset_request_always_succeeds(auth_client):
    """Password reset should always return success to prevent email enumeration."""
    response = auth_client.post(
        "/api/v1/auth/password-reset",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == 200
    assert "reset link" in response.json()["message"]


def test_password_reset_confirm_requires_fields(auth_client):
    response = auth_client.post(
        "/api/v1/auth/password-reset/confirm",
        json={},
    )
    assert response.status_code == 422


def test_password_reset_confirm_rejects_invalid_token(auth_client):
    response = auth_client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "invalid-token", "new_password": "newpassword123"},
    )
    assert response.status_code == 400
    assert "Invalid or expired" in response.json()["detail"]


def test_register_and_login_flow(auth_client):
    """Test the full registration and login flow."""
    # Register
    reg_response = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "flow@example.com", "password": "testpass123"},
    )
    assert reg_response.status_code == 200
    reg_data = reg_response.json()
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    assert reg_data["user"]["email"] == "flow@example.com"
    assert reg_data["user"]["is_premium"] is False

    # Login with same credentials
    login_response = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "flow@example.com", "password": "testpass123"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data

    # Access /me
    me_response = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "flow@example.com"


def test_register_duplicate_email(auth_client):
    """Duplicate registration should fail."""
    auth_client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "testpass123"},
    )
    response = auth_client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "testpass123"},
    )
    assert response.status_code == 409


def test_login_wrong_password(auth_client):
    auth_client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@example.com", "password": "testpass123"},
    )
    response = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


# ── User model tests (updated) ──


def test_user_with_password_hash():
    user = User(email="test@example.com", password_hash="hashed123")
    assert user.password_hash == "hashed123"
    assert user.is_premium is False


def test_user_defaults():
    user = User(email="test@example.com")
    assert user.password_hash == ""
    assert user.created_at is None
    assert user.updated_at is None
