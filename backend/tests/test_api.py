"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code in [200, 503]  # May be degraded if models not loaded


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.skip(reason="Requires database and file upload")
def test_create_job():
    """Test job creation endpoint."""
    # This would require actual file upload
    pass




