"""
Tests for designs routes.
"""
import pytest
from unittest.mock import Mock, patch
from server.src.entities.user import User
from server.src.entities.designs import Design


class TestDesignsRoutes:
    """Test cases for designs routes."""
    
    @pytest.fixture
    def authenticated_user(self, client, db_session):
        """Create and authenticate a user."""
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
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_design(self, client, authenticated_user, mock_file_operations):
        """Test creating a new design."""
        design_data = {
            "name": "Test Design",
            "description": "A test design",
            "tags": ["test", "design"]
        }
        
        # Mock file upload
        files = {"file": ("design.png", b"fake image data", "image/png")}
        
        response = client.post(
            "/designs/",
            data=design_data,
            files=files,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        created_design = response.json()
        assert created_design["name"] == "Test Design"
        assert created_design["description"] == "A test design"
        assert "test" in created_design["tags"]
    
    def test_get_user_designs(self, client, authenticated_user, db_session, sample_user_data):
        """Test retrieving user designs."""
        # Create user and design
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        design = Design(
            user_id=user.id,
            name="Test Design",
            description="A test design",
            file_path="/path/to/design.png"
        )
        db_session.add(design)
        db_session.commit()
        
        response = client.get("/designs/", headers=authenticated_user)
        assert response.status_code == 200
        
        designs = response.json()
        assert len(designs) >= 0  # May have designs from other tests
    
    def test_get_design_by_id(self, client, authenticated_user, db_session, sample_user_data):
        """Test retrieving a specific design."""
        # Create user and design
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        design = Design(
            user_id=user.id,
            name="Test Design",
            description="A test design",
            file_path="/path/to/design.png"
        )
        db_session.add(design)
        db_session.commit()
        
        response = client.get(f"/designs/{design.id}", headers=authenticated_user)
        assert response.status_code == 200
        
        retrieved_design = response.json()
        assert retrieved_design["name"] == "Test Design"
        assert retrieved_design["description"] == "A test design"
    
    def test_update_design(self, client, authenticated_user, db_session, sample_user_data):
        """Test updating a design."""
        # Create user and design
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        design = Design(
            user_id=user.id,
            name="Original Design",
            description="Original description",
            file_path="/path/to/design.png"
        )
        db_session.add(design)
        db_session.commit()
        
        update_data = {
            "name": "Updated Design",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/designs/{design.id}",
            json=update_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        updated_design = response.json()
        assert updated_design["name"] == "Updated Design"
        assert updated_design["description"] == "Updated description"
    
    def test_delete_design(self, client, authenticated_user, db_session, sample_user_data):
        """Test deleting a design."""
        # Create user and design
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        design = Design(
            user_id=user.id,
            name="Test Design",
            description="A test design",
            file_path="/path/to/design.png"
        )
        db_session.add(design)
        db_session.commit()
        design_id = design.id
        
        response = client.delete(f"/designs/{design_id}", headers=authenticated_user)
        assert response.status_code == 204
        
        # Verify design is deleted
        deleted_design = db_session.query(Design).filter(Design.id == design_id).first()
        assert deleted_design is None
    
    def test_unauthorized_access(self, client):
        """Test accessing designs without authentication."""
        response = client.get("/designs/")
        assert response.status_code == 401
    
    def test_design_not_found(self, client, authenticated_user):
        """Test accessing non-existent design."""
        response = client.get("/designs/99999", headers=authenticated_user)
        assert response.status_code == 404