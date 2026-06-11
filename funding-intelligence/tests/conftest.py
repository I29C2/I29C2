"""Fixtures comune. La MVP testele de unitate nu ating DB-ul live sau site-uri reale."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
