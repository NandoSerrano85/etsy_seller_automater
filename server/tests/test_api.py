"""
Unit tests for API routes.
"""
import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from server.api.routes import app

client = TestClient(app)

def test_ping_endpoint():
    """Test the ping endpoint."""
    response = client.get("/api/ping")
    assert response.status_code in [200, 400]  # 400 if Etsy API is not configured

def test_oauth_data_endpoint():
    """Test the OAuth data endpoint."""
    response = client.get("/api/oauth-data")
    assert response.status_code == 200
    data = response.json()
    assert "clientId" in data
    assert "redirectUri" in data
    assert "scopes" in data

def test_oauth_data_legacy_endpoint():
    """Test the legacy OAuth data endpoint."""
    response = client.get("/api/oauth-data-legacy")
    assert response.status_code == 200
    data = response.json()
    assert "clientId" in data
    assert "redirectUri" in data
    assert "scopes" in data

def test_frontend_routes():
    """Test frontend route serving."""
    response = client.get("/")
    # Should return either the frontend or a message about frontend not being built
    assert response.status_code in [200, 404]

def test_api_routes_not_served_as_frontend():
    """Test that API routes are not served as frontend."""
    response = client.get("/api/ping")
    assert response.status_code in [200, 400]  # Should not be 404

def test_oauth_routes_not_served_as_frontend():
    """Test that OAuth routes are not served as frontend."""
    response = client.get("/oauth/redirect?code=test")
    assert response.status_code in [200, 400]  # Should not be 404 