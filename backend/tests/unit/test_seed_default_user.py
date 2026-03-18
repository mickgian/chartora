"""Tests for the default user seed script."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import bcrypt
from scripts.seed_default_user import (
    DEFAULT_EMAIL,
    DEFAULT_PASSWORD,
    _hash_password,
    seed,
)


class TestHashPassword:
    def test_returns_valid_bcrypt_hash(self) -> None:
        hashed = _hash_password("testpassword")
        assert bcrypt.checkpw(b"testpassword", hashed.encode("utf-8"))

    def test_different_calls_produce_different_hashes(self) -> None:
        h1 = _hash_password("same")
        h2 = _hash_password("same")
        assert h1 != h2  # bcrypt uses random salt


class TestSeed:
    @patch("scripts.seed_default_user.create_engine")
    def test_inserts_default_user(self, mock_create_engine: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        seed("postgresql://test:test@localhost/test")

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        assert params["email"] == DEFAULT_EMAIL
        assert params["subscription_status"] == "active"
        assert bcrypt.checkpw(
            DEFAULT_PASSWORD.encode("utf-8"),
            params["password_hash"].encode("utf-8"),
        )

    @patch("scripts.seed_default_user.create_engine")
    def test_strips_asyncpg_driver(self, mock_create_engine: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        seed("postgresql+asyncpg://test:test@localhost/test")

        mock_create_engine.assert_called_once_with(
            "postgresql://test:test@localhost/test"
        )


class TestDefaultCredentials:
    def test_email_is_valid(self) -> None:
        assert "@" in DEFAULT_EMAIL
        assert "." in DEFAULT_EMAIL.split("@")[1]

    def test_password_meets_minimum_length(self) -> None:
        assert len(DEFAULT_PASSWORD) >= 8
