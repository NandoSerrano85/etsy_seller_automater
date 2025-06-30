import pytest
from fastapi.testclient import TestClient
from server.api.routes import app

client = TestClient(app)

def test_ping():
    response = client.get('/api/ping')
    assert response.status_code in (200, 401, 403)  # May require auth

def test_oauth_data():
    response = client.get('/api/oauth-data')
    assert response.status_code == 200
    assert 'clientId' in response.json()

def test_register_invalid():
    # Should fail with missing data
    response = client.post('/api/register', json={})
    assert response.status_code == 422 