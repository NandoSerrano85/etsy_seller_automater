#!/usr/bin/env python3
"""
Test script to verify mockup utils migration worked correctly
"""

import sys
import os

# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

def test_mockup_utils_import():
    """Test that the mockup utils can be imported correctly"""
    try:
        # Test utils import
        from src.utils.mockups_util import (
            MockupTemplateCache,
            MockupImageProcessor,
            find_png_files,
            process_design_image,
            create_mockup_images
        )
        print("✓ Mockup utils imported successfully")
        
        # Test class instantiation
        cache = MockupTemplateCache()
        print("✓ MockupTemplateCache created successfully")
        
        # Test MockupImageProcessor
        mockup_paths = ["/path/to/mockup1.png", "/path/to/mockup2.png"]
        design_path = "/path/to/designs/"
        processor = MockupImageProcessor(mockup_paths, design_path)
        print("✓ MockupImageProcessor created successfully")
        
        # Test utility functions
        test_dir = "/tmp/test_mockups"
        os.makedirs(test_dir, exist_ok=True)
        png_files, png_names = find_png_files(test_dir)
        print("✓ find_png_files function works correctly")
        
        # Clean up
        os.rmdir(test_dir)
        
        print("\n🎉 All mockup utils imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error importing mockup utils: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_import():
    """Test that the service can import the utils correctly"""
    try:
        # Test service import
        from src.routes.mockups.service import create_mockup_image
        print("✓ Service imports utils correctly")
        
        # Test that the function exists
        assert hasattr(create_mockup_image, '__call__'), "create_mockup_image is not callable"
        print("✓ create_mockup_image function exists")
        
        print("\n🎉 Service imports work correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing service imports: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_utils_structure():
    """Test that the utils file has the correct structure"""
    try:
        from src.utils.mockups_util import create_mockup_images
        
        # Test function signature
        import inspect
        sig = inspect.signature(create_mockup_images)
        params = list(sig.parameters.keys())
        
        expected_params = [
            'design_file_path',
            'template_name', 
            'user_id',
            'mockup_id',
            'root_path',
            'starting_name',
            'db_session'
        ]
        
        for param in expected_params:
            assert param in params, f"Missing parameter: {param}"
        
        print("✓ create_mockup_images has correct parameters")
        return True
        
    except Exception as e:
        print(f"❌ Error testing utils structure: {e}")
        return False

if __name__ == "__main__":
    print("Testing mockup utils migration...\n")
    
    tests = [
        test_mockup_utils_import,
        test_service_import,
        test_utils_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Mockup utils migration successful.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 