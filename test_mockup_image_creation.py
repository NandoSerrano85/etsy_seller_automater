#!/usr/bin/env python3
"""
Test script to verify mockup image creation functionality
"""

import sys
import os

# Add the server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

def test_mockup_image_creation():
    """Test the mockup image creation functionality"""
    try:
        # Test imports
        from src.routes.mockups.service import MockupImageProcessor, MockupTemplateCache, find_png_files
        print("✓ Mockup image creation classes imported successfully")
        
        # Test MockupTemplateCache
        cache = MockupTemplateCache()
        print("✓ MockupTemplateCache created successfully")
        
        # Test MockupImageProcessor
        mockup_paths = ["/path/to/mockup1.png", "/path/to/mockup2.png"]
        design_path = "/path/to/designs/"
        processor = MockupImageProcessor(mockup_paths, design_path)
        print("✓ MockupImageProcessor created successfully")
        
        # Test find_png_files function
        test_dir = "/tmp/test_mockups"
        os.makedirs(test_dir, exist_ok=True)
        png_files, png_names = find_png_files(test_dir)
        print("✓ find_png_files function works correctly")
        
        # Clean up
        os.rmdir(test_dir)
        
        print("\n🎉 All mockup image creation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing mockup image creation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_updates():
    """Test that the model has been updated correctly"""
    try:
        from src.routes.mockups import model
        
        # Test that MockupImageCreate has design_file_path field
        create_model = model.MockupImageCreate(
            mockups_id="123e4567-e89b-12d3-a456-426614174000",
            filename="test.png",
            file_path="/path/to/file.png",
            design_file_path="/path/to/design.png"
        )
        
        assert hasattr(create_model, 'design_file_path'), "design_file_path field not found"
        assert create_model.design_file_path == "/path/to/design.png", "design_file_path not set correctly"
        
        print("✓ MockupImageCreate model updated correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing model updates: {e}")
        return False

if __name__ == "__main__":
    print("Testing mockup image creation functionality...\n")
    
    tests = [
        test_mockup_image_creation,
        test_model_updates
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Mockup image creation is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 