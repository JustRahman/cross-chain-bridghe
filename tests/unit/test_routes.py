"""Tests for route endpoints"""
import pytest
from fastapi.testclient import TestClient


def test_route_quote_requires_auth(client: TestClient):
    """Test that route quote requires API key"""
    response = client.post(
        "/api/v1/routes/quote",
        json={
            "source_chain": "ethereum",
            "destination_chain": "arbitrum",
            "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "amount": "1000000000"
        }
    )
    assert response.status_code == 401


def test_route_quote_with_api_key(client: TestClient, mock_api_key: str):
    """Test route quote with valid API key"""
    response = client.post(
        "/api/v1/routes/quote",
        json={
            "source_chain": "ethereum",
            "destination_chain": "arbitrum",
            "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "amount": "1000000000"
        },
        headers={"X-API-Key": mock_api_key}
    )
    assert response.status_code == 200

    data = response.json()
    assert "routes" in data
    assert "quote_id" in data
    assert "expires_at" in data
    assert len(data["routes"]) > 0


def test_route_quote_invalid_chain(client: TestClient, mock_api_key: str):
    """Test route quote with invalid chain"""
    response = client.post(
        "/api/v1/routes/quote",
        json={
            "source_chain": "invalid_chain",
            "destination_chain": "arbitrum",
            "source_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "destination_token": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "amount": "1000000000"
        },
        headers={"X-API-Key": mock_api_key}
    )
    assert response.status_code == 422  # Validation error
