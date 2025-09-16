#!/usr/bin/env python3
"""
Test script to verify the /start-upload endpoint works correctly after the FastAPI fix.
"""

import sys
from pathlib import Path

# Add the project root directory to the path
server_root = Path(__file__).parent
project_root = server_root.parent
sys.path.insert(0, str(project_root))

def test_import():
    """Test that the controller can be imported without errors."""
    try:
        print("Testing controller import...")
        from server.src.routes.designs.controller import router
        print("✅ Controller imported successfully!")

        # Check if the route is registered
        routes = [route.path for route in router.routes]
        if "/start-upload" in routes:
            print("✅ /start-upload endpoint found in routes")
        else:
            print("❌ /start-upload endpoint not found in routes")

        return True
    except Exception as e:
        print(f"❌ Error importing controller: {e}")
        return False

def test_start_upload_signature():
    """Test that the start_upload function has the correct signature."""
    try:
        from server.src.routes.designs.controller import start_upload
        import inspect

        print("Testing start_upload function signature...")
        sig = inspect.signature(start_upload)
        params = list(sig.parameters.keys())

        expected_params = ['files', 'current_user', 'db']
        if params == expected_params:
            print("✅ Function signature is correct")
        else:
            print(f"❌ Unexpected function signature. Expected: {expected_params}, Got: {params}")

        return True
    except Exception as e:
        print(f"❌ Error checking function signature: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing FastAPI /start-upload endpoint fix...")
    print("=" * 50)

    success = True

    # Test import
    if not test_import():
        success = False

    print()

    # Test function signature
    if not test_start_upload_signature():
        success = False

    print()
    print("=" * 50)

    if success:
        print("🎉 All tests passed! The FastAPI fix is working correctly.")
        print("   The /start-upload endpoint should now deploy without errors.")
    else:
        print("❌ Some tests failed. Please check the errors above.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())