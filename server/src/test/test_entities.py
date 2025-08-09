"""
Tests for entity models.
"""
import pytest
from datetime import datetime
from server.src.entities.user import User
from server.src.entities.designs import Design
from server.src.entities.template import Template
from server.src.entities.mockup import Mockup
from server.src.entities.canvas_config import CanvasConfig
from server.src.entities.size_config import SizeConfig
from server.src.entities.third_party_oauth import ThirdPartyOAuth


class TestUserEntity:
    """Test cases for User entity."""
    
    def test_user_creation(self, db_session):
        """Test creating a user entity."""
        user = User(
            username="testuser",
            email="test@example.com",
            etsy_user_id="123456"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.etsy_user_id == "123456"
        assert user.created_at is not None
    
    def test_user_string_representation(self):
        """Test user string representation."""
        user = User(username="testuser", email="test@example.com")
        assert str(user) == "testuser"


class TestDesignEntity:
    """Test cases for Design entity."""
    
    def test_design_creation(self, db_session, sample_user_data):
        """Test creating a design entity."""
        # First create a user
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
        
        assert design.id is not None
        assert design.user_id == user.id
        assert design.name == "Test Design"
        assert design.description == "A test design"
        assert design.file_path == "/path/to/design.png"
        assert design.created_at is not None


class TestTemplateEntity:
    """Test cases for Template entity."""
    
    def test_template_creation(self, db_session):
        """Test creating a template entity."""
        template = Template(
            name="Test Template",
            description="A test template",
            file_path="/path/to/template.png",
            category="t-shirt"
        )
        db_session.add(template)
        db_session.commit()
        
        assert template.id is not None
        assert template.name == "Test Template"
        assert template.description == "A test template"
        assert template.file_path == "/path/to/template.png"
        assert template.category == "t-shirt"


class TestMockupEntity:
    """Test cases for Mockup entity."""
    
    def test_mockup_creation(self, db_session, sample_user_data):
        """Test creating a mockup entity."""
        # First create a user
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        mockup = Mockup(
            user_id=user.id,
            name="Test Mockup",
            template_id=1,
            design_id=1,
            file_path="/path/to/mockup.png"
        )
        db_session.add(mockup)
        db_session.commit()
        
        assert mockup.id is not None
        assert mockup.user_id == user.id
        assert mockup.name == "Test Mockup"
        assert mockup.template_id == 1
        assert mockup.design_id == 1


class TestCanvasConfigEntity:
    """Test cases for CanvasConfig entity."""
    
    def test_canvas_config_creation(self, db_session):
        """Test creating a canvas config entity."""
        config = CanvasConfig(
            name="Standard Canvas",
            width=1000,
            height=1000,
            dpi=300
        )
        db_session.add(config)
        db_session.commit()
        
        assert config.id is not None
        assert config.name == "Standard Canvas"
        assert config.width == 1000
        assert config.height == 1000
        assert config.dpi == 300


class TestSizeConfigEntity:
    """Test cases for SizeConfig entity."""
    
    def test_size_config_creation(self, db_session):
        """Test creating a size config entity."""
        size_config = SizeConfig(
            name="Medium",
            width=500,
            height=600,
            category="apparel"
        )
        db_session.add(size_config)
        db_session.commit()
        
        assert size_config.id is not None
        assert size_config.name == "Medium"
        assert size_config.width == 500
        assert size_config.height == 600
        assert size_config.category == "apparel"


class TestThirdPartyOAuthEntity:
    """Test cases for ThirdPartyOAuth entity."""
    
    def test_oauth_creation(self, db_session, sample_user_data):
        """Test creating a third party oauth entity."""
        # First create a user
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        oauth = ThirdPartyOAuth(
            user_id=user.id,
            provider="etsy",
            access_token="test_token",
            refresh_token="test_refresh"
        )
        db_session.add(oauth)
        db_session.commit()
        
        assert oauth.id is not None
        assert oauth.user_id == user.id
        assert oauth.provider == "etsy"
        assert oauth.access_token == "test_token"
        assert oauth.refresh_token == "test_refresh"
