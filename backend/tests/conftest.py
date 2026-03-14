import pytest
from fastapi.testclient import TestClient

from src.adapters.api.main import create_app
from src.config.settings import Settings


@pytest.fixture
def settings():
    return Settings(database_url="sqlite+aiosqlite:///test.db")


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    return TestClient(app)
