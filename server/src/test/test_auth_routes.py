"""
Tests for authentication routes.
"""
import pytest
from unittest.mock import Mock, patch
from server.src.routes.auth.controller import router as auth_router
from server.src.entities.user import User


class TestAuthRoutes:
    """Test cases for authentication routes."""
    
    def test_register_user_success(self, client, db_session):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Verify user was created in database
        user = db_session.query(User).filter(User.email == "new@example.com").first()
        assert user is not None
        assert user.username == "newuser"
    
    def test_register_user_duplicate_email(self, client, db_session, sample_user_data):
        """Test registration with duplicate email."""
        # Create existing user
        existing_user = User(**sample_user_data)
        db_session.add(existing_user)
        db_session.commit()
        
        user_data = {
            "username": "newuser",
            "email": "test@example.com",  # Same as existing user
            "password": "testpass123"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_login_success(self, client, db_session):
        """Test successful login."""
        # Create user first
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
        client.post("/auth/register", json=user_data)
        
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "token_type" in response.json()
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpass"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_get_current_user(self, client, db_session):
        """Test getting current user profile."""
        # Create and login user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
        client.post("/auth/register", json=user_data)
        
        login_response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        
        # Get user profile
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        user_profile = response.json()
        assert user_profile["email"] == "test@example.com"
        assert user_profile["username"] == "testuser"
    
    def test_logout(self, client, db_session):
        """Test user logout."""
        # Create and login user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
        client.post("/auth/register", json=user_data)
        
        login_response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/auth/logout", headers=headers)
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
    
    def test_refresh_token(self, client, db_session):
        """Test token refresh functionality."""
        # Create and login user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123"
        }
        client.post("/auth/register", json=user_data)
        
        login_response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        refresh_token = login_response.json().get("refresh_token")
        
        if refresh_token:
            response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
            assert response.status_code == 200
            assert "access_token" in response.json()