#!/usr/bin/env python3
"""
Test script for the mask creator functionality.
This script tests the mask utilities and API endpoints.
"""

import json
import os
import sys

# Add the server directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

def test_mask_utils():
    """Test the mask utilities functions."""
    print("Testing mask utilities...")
    
    try:
        from server.engine.mask_utils import validate_mask_points, save_mask_data, load_mask_data
        
        # Test data
        test_points = [
            {"x": 100.0, "y": 100.0},
            {"x": 200.0, "y": 100.0},
            {"x": 200.0, "y": 200.0},
            {"x": 100.0, "y": 200.0}
        ]
        
        # Test validation
        print("✓ Testing point validation...")
        assert validate_mask_points(test_points), "Point validation failed"
        assert not validate_mask_points([]), "Empty points should be invalid"
        assert not validate_mask_points([{"x": 100.0}]), "Incomplete points should be invalid"
        
        # Test saving and loading
        print("✓ Testing save and load functionality...")
        test_file = "test_mask_data.json"
        file_path = save_mask_data([test_points], "UVDTF 16oz", test_file)
        
        assert os.path.exists(file_path), "Mask file was not created"
        
        masks, points = load_mask_data(file_path, "UVDTF 16oz")
        assert len(masks) == 1, "Should have loaded 1 mask"
        assert len(points) == 1, "Should have loaded 1 set of points"
        
        # Clean up
        os.remove(test_file)
        print("✓ All mask utility tests passed!")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
    
    return True

def test_api_endpoint():
    """Test the API endpoint structure."""
    print("\nTesting API endpoint structure...")
    
    try:
        from server.api.routes import MaskPoint, MaskData
        
        # Test Pydantic models
        print("✓ Testing Pydantic models...")
        point = MaskPoint(x=100, y=100)
        assert point.x == 100 and point.y == 100, "MaskPoint model failed"
        
        mask_data = MaskData(
            masks=[[{"x": 100, "y": 100}, {"x": 200, "y": 200}, {"x": 150, "y": 150}]],
            imageType="UVDTF 16oz"
        )
        assert len(mask_data.masks) == 1, "MaskData model failed"
        assert mask_data.imageType == "UVDTF 16oz", "ImageType not set correctly"
        
        print("✓ All API endpoint tests passed!")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
    
    return True

def test_mockup_engine():
    """Test that the mockup engine doesn't use Metal GPU."""
    print("\nTesting mockup engine...")
    
    try:
        from server.engine.mockup_engine import USE_METAL
        
        print("✓ Testing Metal GPU usage...")
        assert USE_METAL == False, "Metal GPU should be disabled"
        print("✓ Metal GPU is correctly disabled!")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Running mask creator tests...\n")
    
    tests = [
        test_mask_utils,
        test_api_endpoint,
        test_mockup_engine
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The mask creator is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 