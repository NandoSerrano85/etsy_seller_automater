"""
Pytest configuration for Etsy Seller Automaker tests.
"""
import pytest
import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Add the server directory to the Python path
server_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, server_path)

@pytest.fixture
def sample_mask_points():
    """Sample mask points for testing."""
    return [
        {"x": 100, "y": 100},
        {"x": 200, "y": 100},
        {"x": 200, "y": 200},
        {"x": 100, "y": 200}
    ]

@pytest.fixture
def sample_mask_data():
    """Sample mask data for testing."""
    return {
        "masks": [
            [
                {"x": 100, "y": 100},
                {"x": 200, "y": 100},
                {"x": 200, "y": 200},
                {"x": 100, "y": 200}
            ]
        ],
        "imageType": "UVDTF 16oz"
    } 