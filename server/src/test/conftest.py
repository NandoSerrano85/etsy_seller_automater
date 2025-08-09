"""
Pytest configuration and fixtures for server tests.
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from server.src.database.core import Base, get_db
from server.main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    """Create a database session for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    """Create a test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_etsy_api():
    """Mock Etsy API responses."""
    with patch('server.src.utils.etsy_api_engine.EtsyAPIEngine') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "etsy_user_id": "123456",
        "access_token": "test_token",
        "refresh_token": "test_refresh_token"
    }

@pytest.fixture
def sample_design_data():
    """Sample design data for testing."""
    return {
        "id": 1,
        "user_id": 1,
        "name": "Test Design",
        "description": "A test design",
        "file_path": "/path/to/design.png",
        "tags": ["test", "design"]
    }

@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return {
        "id": 1,
        "name": "Test Template",
        "description": "A test template",
        "file_path": "/path/to/template.png",
        "category": "t-shirt"
    }

@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
        "id": 1,
        "user_id": 1,
        "etsy_order_id": "123456789",
        "status": "pending",
        "total_amount": 29.99,
        "items": []
    }

@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing."""
    with patch('builtins.open'), \
         patch('os.path.exists', return_value=True), \
         patch('os.makedirs'), \
         patch('shutil.copy2'):
        yield

@pytest.fixture
def mock_image_processing():
    """Mock image processing operations."""
    with patch('PIL.Image.open') as mock_open, \
         patch('PIL.Image.new') as mock_new:
        mock_image = Mock()
        mock_image.size = (1000, 1000)
        mock_image.save = Mock()
        mock_image.resize = Mock(return_value=mock_image)
        mock_image.crop = Mock(return_value=mock_image)
        mock_open.return_value = mock_image
        mock_new.return_value = mock_image
        yield mock_image
