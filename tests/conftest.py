import pytest
from fastapi.testclient import TestClient

from src.config import Settings, get_settings
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_settings() -> Settings:
    return get_settings()
