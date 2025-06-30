"""
Unit tests for mask utilities.
"""
import pytest
import os
import sys
import tempfile
import json

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from server.engine.mask_utils import save_mask_data, validate_mask_points

def test_validate_mask_points_valid():
    """Test validation of valid mask points."""
    valid_points = [
        {"x": 100, "y": 100},
        {"x": 200, "y": 100},
        {"x": 200, "y": 200},
        {"x": 100, "y": 200}
    ]
    
    assert validate_mask_points(valid_points) == True

def test_validate_mask_points_insufficient():
    """Test validation with insufficient points."""
    insufficient_points = [
        {"x": 100, "y": 100},
        {"x": 200, "y": 100}
    ]
    
    assert validate_mask_points(insufficient_points) == False

def test_validate_mask_points_empty():
    """Test validation with empty points list."""
    assert validate_mask_points([]) == False

def test_validate_mask_points_invalid_structure():
    """Test validation with invalid point structure."""
    invalid_points = [
        {"x": 100},  # Missing y
        {"y": 100},  # Missing x
        {"x": 200, "y": 100}
    ]
    
    assert validate_mask_points(invalid_points) == False

def test_save_mask_data():
    """Test saving mask data to file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        masks = [
            [
                {"x": 100, "y": 100},
                {"x": 200, "y": 100},
                {"x": 200, "y": 200},
                {"x": 100, "y": 200}
            ]
        ]
        image_type = "UVDTF 16oz"
        
        # Test saving
        result = save_mask_data(masks, image_type, temp_dir)
        assert result == True
        
        # Check if file was created
        expected_filename = f"{image_type.replace(' ', '_').lower()}_masks.json"
        file_path = os.path.join(temp_dir, expected_filename)
        assert os.path.exists(file_path)
        
        # Check file content
        with open(file_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["imageType"] == image_type
        assert saved_data["masks"] == masks

def test_save_mask_data_invalid_directory():
    """Test saving mask data to invalid directory."""
    masks = [
        [
            {"x": 100, "y": 100},
            {"x": 200, "y": 100},
            {"x": 200, "y": 200},
            {"x": 100, "y": 200}
        ]
    ]
    image_type = "UVDTF 16oz"
    
    # Test with non-existent directory
    result = save_mask_data(masks, image_type, "/non/existent/path")
    assert result == False 