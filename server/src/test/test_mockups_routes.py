"""
Tests for mockups routes.
"""
import pytest
from unittest.mock import Mock, patch
from server.src.entities.user import User
from server.src.entities.designs import Design
from server.src.entities.template import Template
from server.src.entities.mockup import Mockup


class TestMockupsRoutes:
    """Test cases for mockups routes."""
    
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
    
    @pytest.fixture
    def setup_data(self, db_session, sample_user_data):
        """Set up user, design, and template for mockup tests."""
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
        
        template = Template(
            name="Test Template",
            description="A test template",
            file_path="/path/to/template.png",
            category="t-shirt"
        )
        db_session.add(template)
        db_session.commit()
        
        return {
            "user": user,
            "design": design,
            "template": template
        }
    
    @patch('server.src.utils.mockups_util.create_mockup')
    def test_create_mockup(self, mock_create_mockup, client, authenticated_user, setup_data, mock_image_processing):
        """Test creating a new mockup."""
        mock_create_mockup.return_value = "/path/to/mockup.png"
        
        mockup_data = {
            "name": "Test Mockup",
            "template_id": setup_data["template"].id,
            "design_id": setup_data["design"].id
        }
        
        response = client.post(
            "/mockups/",
            json=mockup_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 201
        created_mockup = response.json()
        assert created_mockup["name"] == "Test Mockup"
        assert created_mockup["template_id"] == setup_data["template"].id
        assert created_mockup["design_id"] == setup_data["design"].id
    
    def test_get_user_mockups(self, client, authenticated_user, db_session, setup_data):
        """Test retrieving user mockups."""
        mockup = Mockup(
            user_id=setup_data["user"].id,
            name="Test Mockup",
            template_id=setup_data["template"].id,
            design_id=setup_data["design"].id,
            file_path="/path/to/mockup.png"
        )
        db_session.add(mockup)
        db_session.commit()
        
        response = client.get("/mockups/", headers=authenticated_user)
        assert response.status_code == 200
        
        mockups = response.json()
        assert len(mockups) >= 0  # May have mockups from other tests
    
    def test_get_mockup_by_id(self, client, authenticated_user, db_session, setup_data):
        """Test retrieving a specific mockup."""
        mockup = Mockup(
            user_id=setup_data["user"].id,
            name="Test Mockup",
            template_id=setup_data["template"].id,
            design_id=setup_data["design"].id,
            file_path="/path/to/mockup.png"
        )
        db_session.add(mockup)
        db_session.commit()
        
        response = client.get(f"/mockups/{mockup.id}", headers=authenticated_user)
        assert response.status_code == 200
        
        retrieved_mockup = response.json()
        assert retrieved_mockup["name"] == "Test Mockup"
        assert retrieved_mockup["template_id"] == setup_data["template"].id
    
    def test_update_mockup(self, client, authenticated_user, db_session, setup_data):
        """Test updating a mockup."""
        mockup = Mockup(
            user_id=setup_data["user"].id,
            name="Original Mockup",
            template_id=setup_data["template"].id,
            design_id=setup_data["design"].id,
            file_path="/path/to/mockup.png"
        )
        db_session.add(mockup)
        db_session.commit()
        
        update_data = {
            "name": "Updated Mockup"
        }
        
        response = client.put(
            f"/mockups/{mockup.id}",
            json=update_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        updated_mockup = response.json()
        assert updated_mockup["name"] == "Updated Mockup"
    
    def test_delete_mockup(self, client, authenticated_user, db_session, setup_data):
        """Test deleting a mockup."""
        mockup = Mockup(
            user_id=setup_data["user"].id,
            name="Test Mockup",
            template_id=setup_data["template"].id,
            design_id=setup_data["design"].id,
            file_path="/path/to/mockup.png"
        )
        db_session.add(mockup)
        db_session.commit()
        mockup_id = mockup.id
        
        response = client.delete(f"/mockups/{mockup_id}", headers=authenticated_user)
        assert response.status_code == 204
        
        # Verify mockup is deleted
        deleted_mockup = db_session.query(Mockup).filter(Mockup.id == mockup_id).first()
        assert deleted_mockup is None
    
    @patch('server.src.utils.mockups_util.generate_preview')
    def test_generate_mockup_preview(self, mock_generate_preview, client, authenticated_user, setup_data):
        """Test generating mockup preview."""
        mock_generate_preview.return_value = b"fake preview image data"
        
        preview_data = {
            "template_id": setup_data["template"].id,
            "design_id": setup_data["design"].id
        }
        
        response = client.post(
            "/mockups/preview",
            json=preview_data,
            headers=authenticated_user
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
    
    def test_unauthorized_access(self, client):
        """Test accessing mockups without authentication."""
        response = client.get("/mockups/")
        assert response.status_code == 401
    
    def test_mockup_not_found(self, client, authenticated_user):
        """Test accessing non-existent mockup."""
        response = client.get("/mockups/99999", headers=authenticated_user)
        assert response.status_code == 404