"""Tests for health check endpoints"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test basic health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_liveness_check(client: TestClient):
    """Test Kubernetes liveness probe"""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_root_endpoint(client: TestClient):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "operational"
