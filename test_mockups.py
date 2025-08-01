#!/usr/bin/env python3
"""
Simple test script to verify mockups files are working correctly
"""

import sys
import os

# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

def test_mockups_imports():
    """Test that all mockups files can be imported without errors"""
    try:
        # Test model imports
        from src.routes.mockups import model
        print("✓ Mockups model imported successfully")
        
        # Test service imports
        from src.routes.mockups import service
        print("✓ Mockups service imported successfully")
        
        # Test controller imports
        from src.routes.mockups import controller
        print("✓ Mockups controller imported successfully")
        
        # Test entity imports
        from src.entities.mockup import Mockups, MockupImage, MockupMaskData
        print("✓ Mockups entities imported successfully")
        
        # Test message imports
        from src.message import (
            MockupNotFoundError,
            MockupCreateError,
            MockupGetAllError,
            MockupGetByIdError,
            MockupUpdateError,
            MockupDeleteError,
            MockupImageNotFoundError,
            MockupImageCreateError,
            MockupImageGetAllError,
            MockupImageGetByIdError,
            MockupImageUpdateError,
            MockupImageDeleteError,
            MockupMaskDataNotFoundError,
            MockupMaskDataCreateError,
            MockupMaskDataGetAllError,
            MockupMaskDataGetByIdError,
            MockupMaskDataUpdateError,
            MockupMaskDataDeleteError
        )
        print("✓ Mockups error classes imported successfully")
        
        print("\n🎉 All mockups imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error importing mockups files: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_structure():
    """Test that the model classes have the expected structure"""
    try:
        from src.routes.mockups import model
        
        # Test that key model classes exist
        assert hasattr(model, 'MockupsCreate'), "MockupsCreate not found"
        assert hasattr(model, 'MockupsResponse'), "MockupsResponse not found"
        assert hasattr(model, 'MockupImageCreate'), "MockupImageCreate not found"
        assert hasattr(model, 'MockupImageResponse'), "MockupImageResponse not found"
        assert hasattr(model, 'MockupMaskDataCreate'), "MockupMaskDataCreate not found"
        assert hasattr(model, 'MockupMaskDataResponse'), "MockupMaskDataResponse not found"
        
        print("✓ Mockups model structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error testing model structure: {e}")
        return False

def test_service_functions():
    """Test that the service functions exist"""
    try:
        from src.routes.mockups import service
        
        # Test that key service functions exist
        assert hasattr(service, 'create_mockup'), "create_mockup not found"
        assert hasattr(service, 'get_mockups_by_user_id'), "get_mockups_by_user_id not found"
        assert hasattr(service, 'get_mockup_by_id'), "get_mockup_by_id not found"
        assert hasattr(service, 'update_mockup'), "update_mockup not found"
        assert hasattr(service, 'delete_mockup'), "delete_mockup not found"
        
        assert hasattr(service, 'create_mockup_image'), "create_mockup_image not found"
        assert hasattr(service, 'get_mockup_images_by_mockup_id'), "get_mockup_images_by_mockup_id not found"
        assert hasattr(service, 'get_mockup_image_by_id'), "get_mockup_image_by_id not found"
        assert hasattr(service, 'update_mockup_image'), "update_mockup_image not found"
        assert hasattr(service, 'delete_mockup_image'), "delete_mockup_image not found"
        
        assert hasattr(service, 'create_mockup_mask_data'), "create_mockup_mask_data not found"
        assert hasattr(service, 'get_mockup_mask_data_by_image_id'), "get_mockup_mask_data_by_image_id not found"
        assert hasattr(service, 'get_mockup_mask_data_by_id'), "get_mockup_mask_data_by_id not found"
        assert hasattr(service, 'update_mockup_mask_data'), "update_mockup_mask_data not found"
        assert hasattr(service, 'delete_mockup_mask_data'), "delete_mockup_mask_data not found"
        
        print("✓ Mockups service functions exist")
        return True
        
    except Exception as e:
        print(f"❌ Error testing service functions: {e}")
        return False

def test_controller_routes():
    """Test that the controller routes exist"""
    try:
        from src.routes.mockups import controller
        
        # Test that router exists
        assert hasattr(controller, 'router'), "router not found"
        
        # Test that key route functions exist
        assert hasattr(controller, 'create_mockup'), "create_mockup route not found"
        assert hasattr(controller, 'get_mockups'), "get_mockups route not found"
        assert hasattr(controller, 'get_mockup'), "get_mockup route not found"
        assert hasattr(controller, 'update_mockup'), "update_mockup route not found"
        assert hasattr(controller, 'delete_mockup'), "delete_mockup route not found"
        
        print("✓ Mockups controller routes exist")
        return True
        
    except Exception as e:
        print(f"❌ Error testing controller routes: {e}")
        return False

if __name__ == "__main__":
    print("Testing mockups files...\n")
    
    tests = [
        test_mockups_imports,
        test_model_structure,
        test_service_functions,
        test_controller_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Mockups files are working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 