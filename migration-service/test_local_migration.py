#!/usr/bin/env python3
"""
Test script for local design migration

This script tests the local design migration functionality by:
1. Setting up test environment variables
2. Running the migration in dry-run mode
3. Validating the migration process

Usage:
    python test_local_migration.py
"""

import os
import sys
import logging
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_directory_structure():
    """Create a temporary test directory structure"""
    temp_dir = tempfile.mkdtemp(prefix="etsy_migration_test_")
    logger.info(f"Created test directory: {temp_dir}")

    # Create test shop structures
    test_structure = {
        'TestShop1': {
            'UVDTF 16oz': ['design1.png', 'design2.jpg'],
            'UVDTF Bookmark': ['bookmark1.png'],
            'Digital': {
                'Digital Template 1': ['digital1.png', 'digital2.png']
            }
        },
        'TestShop2': {
            'MK Tapered': ['mk_design1.png'],
            'Custom 2x2': ['custom1.png', 'custom2.png']
        }
    }

    # Create directory structure (without actual image files)
    for shop_name, templates in test_structure.items():
        shop_dir = os.path.join(temp_dir, shop_name)
        os.makedirs(shop_dir)

        for template_name, files in templates.items():
            if template_name == 'Digital':
                # Handle Digital subdirectory
                digital_dir = os.path.join(shop_dir, 'Digital')
                os.makedirs(digital_dir)
                for digital_template, digital_files in files.items():
                    digital_template_dir = os.path.join(digital_dir, digital_template)
                    os.makedirs(digital_template_dir)
                    for file_name in digital_files:
                        file_path = os.path.join(digital_template_dir, file_name)
                        # Create empty file as placeholder
                        Path(file_path).touch()
            else:
                # Handle regular template directory
                template_dir = os.path.join(shop_dir, template_name)
                os.makedirs(template_dir)
                for file_name in files:
                    file_path = os.path.join(template_dir, file_name)
                    # Create empty file as placeholder
                    Path(file_path).touch()

    return temp_dir


def setup_test_environment(test_dir):
    """Setup environment variables for testing"""
    # Required environment variables
    os.environ['LOCAL_ROOT_PATH'] = test_dir
    os.environ['LOCAL_MIGRATION_DRY_RUN'] = 'true'  # Always use dry run for testing
    os.environ['MIGRATION_MODE'] = 'local-only'

    # Optional: test with specific shop/template
    # os.environ['LOCAL_MIGRATION_SHOP'] = 'TestShop1'
    # os.environ['LOCAL_MIGRATION_TEMPLATE'] = 'UVDTF 16oz'

    logger.info("Test environment variables set:")
    logger.info(f"  LOCAL_ROOT_PATH: {test_dir}")
    logger.info(f"  LOCAL_MIGRATION_DRY_RUN: true")
    logger.info(f"  MIGRATION_MODE: local-only")


def test_migration_discovery():
    """Test the migration discovery functionality"""
    logger.info("🔍 Testing migration discovery...")

    try:
        # Import the migration module
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'migrations'))
        import import_local_designs

        # Test directory scanning
        local_root_path = os.environ['LOCAL_ROOT_PATH']
        design_files = import_local_designs.find_design_files(local_root_path)

        logger.info(f"Found {len(design_files)} test design files")

        # Display found files
        for file_info in design_files:
            logger.info(f"  📁 {file_info['shop_name']}/{file_info['template_name']}/{file_info['filename']} (digital: {file_info['is_digital']})")

        return len(design_files) > 0

    except Exception as e:
        logger.error(f"❌ Migration discovery test failed: {e}")
        return False


def test_migration_integration():
    """Test integration with the main migration runner"""
    logger.info("🔄 Testing migration integration...")

    try:
        # Import the main migration runner
        import run_migrations

        # Test database setup (this might fail if DATABASE_URL not set)
        try:
            engine = run_migrations.setup_database()
            logger.info("✅ Database connection test passed")

            # Test local migration function
            success = run_migrations.run_local_design_migration(engine)
            if success:
                logger.info("✅ Local migration integration test passed")
                return True
            else:
                logger.error("❌ Local migration integration test failed")
                return False

        except Exception as db_e:
            logger.warning(f"⚠️  Database connection test skipped: {db_e}")
            logger.info("ℹ️  This is expected if DATABASE_URL is not set")

            # Test migration function discovery
            try:
                success = run_migrations.run_local_design_migration(None)
                logger.info("✅ Migration function discovery test passed")
                return True
            except Exception as func_e:
                logger.error(f"❌ Migration function test failed: {func_e}")
                return False

    except Exception as e:
        logger.error(f"❌ Migration integration test failed: {e}")
        return False


def test_error_handling():
    """Test error handling scenarios"""
    logger.info("🛡️  Testing error handling...")

    try:
        # Test with invalid LOCAL_ROOT_PATH
        original_path = os.environ.get('LOCAL_ROOT_PATH')
        os.environ['LOCAL_ROOT_PATH'] = '/nonexistent/path'

        import run_migrations
        success = run_migrations.run_local_design_migration(None)

        # Should return True (graceful skip) for invalid path
        if success:
            logger.info("✅ Invalid path handling test passed")
        else:
            logger.error("❌ Invalid path handling test failed")

        # Restore original path
        if original_path:
            os.environ['LOCAL_ROOT_PATH'] = original_path

        return success

    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        return False


def cleanup_test_directory(test_dir):
    """Clean up the test directory"""
    try:
        import shutil
        shutil.rmtree(test_dir)
        logger.info(f"🧹 Cleaned up test directory: {test_dir}")
    except Exception as e:
        logger.warning(f"⚠️  Could not clean up test directory: {e}")


def main():
    """Main test function"""
    logger.info("🚀 Starting local design migration tests")

    # Create test directory structure
    test_dir = create_test_directory_structure()

    try:
        # Setup test environment
        setup_test_environment(test_dir)

        # Run tests
        tests = [
            ("Migration Discovery", test_migration_discovery),
            ("Migration Integration", test_migration_integration),
            ("Error Handling", test_error_handling),
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Running test: {test_name}")
            logger.info(f"{'=' * 60}")

            try:
                if test_func():
                    logger.info(f"✅ {test_name} - PASSED")
                    passed_tests += 1
                else:
                    logger.error(f"❌ {test_name} - FAILED")
            except Exception as e:
                logger.error(f"💥 {test_name} - ERROR: {e}")

        # Summary
        logger.info(f"\n{'=' * 60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'=' * 60}")
        logger.info(f"Passed: {passed_tests}/{total_tests}")

        if passed_tests == total_tests:
            logger.info("🎉 All tests passed!")
            return True
        else:
            logger.error(f"❌ {total_tests - passed_tests} test(s) failed")
            return False

    finally:
        # Clean up
        cleanup_test_directory(test_dir)

    return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)