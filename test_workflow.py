#!/usr/bin/env python3
"""
Test script for Image Upload Workflow

This script demonstrates how to use the ImageUploadWorkflow system
and can be used to test the complete pipeline.
"""

import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add server directory to path
sys.path.insert(0, '/Users/fserrano/Documents/Projects/etsy_seller_automater/server/src')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_workflow_dependencies():
    """Test if all workflow dependencies are available"""
    try:
        from services.image_upload_workflow import (
            DEPENDENCIES_AVAILABLE,
            NAS_AVAILABLE,
            MOCKUP_SERVICE_AVAILABLE,
            create_workflow
        )

        logger.info("🔍 Checking workflow dependencies...")
        logger.info(f"   ✅ Image processing dependencies: {DEPENDENCIES_AVAILABLE}")
        logger.info(f"   📤 NAS storage available: {NAS_AVAILABLE}")
        logger.info(f"   🎨 Mockup service available: {MOCKUP_SERVICE_AVAILABLE}")

        if not DEPENDENCIES_AVAILABLE:
            logger.warning("⚠️  Core image processing dependencies missing. Install: pip install pillow imagehash sqlalchemy")
            return False

        return True

    except ImportError as e:
        logger.error(f"❌ Failed to import workflow: {e}")
        return False

def create_test_images():
    """Create test image data for workflow testing"""
    from services.image_upload_workflow import UploadedImage
    from PIL import Image
    from io import BytesIO
    import uuid

    test_images = []

    # Create 3 test images with different colors
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue

    for i, color in enumerate(colors):
        # Create a simple colored square
        img = Image.new('RGB', (500, 500), color)

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        content = buffer.getvalue()

        # Create UploadedImage instance
        uploaded_image = UploadedImage(
            original_filename=f"test_image_{i+1}.png",
            content=content,
            size=len(content),
            upload_time=datetime.now(timezone.utc),
            user_id="test_user_123",
            template_id="test_template"
        )

        test_images.append(uploaded_image)

    # Create a duplicate image (same as first)
    duplicate_img = Image.new('RGB', (500, 500), colors[0])
    buffer = BytesIO()
    duplicate_img.save(buffer, format='PNG')
    duplicate_content = buffer.getvalue()

    duplicate_image = UploadedImage(
        original_filename="duplicate_image.png",
        content=duplicate_content,
        size=len(duplicate_content),
        upload_time=datetime.now(timezone.utc),
        user_id="test_user_123",
        template_id="test_template"
    )

    test_images.append(duplicate_image)

    logger.info(f"📸 Created {len(test_images)} test images (including 1 duplicate)")
    return test_images

def test_workflow():
    """Test the complete workflow with sample data"""
    try:
        from services.image_upload_workflow import create_workflow

        logger.info("🚀 Starting workflow test...")

        # Create test images
        test_images = create_test_images()

        # Create mock database session (for testing without actual database)
        class MockSession:
            def execute(self, query, params=None):
                class MockResult:
                    def fetchall(self): return []
                    def fetchone(self): return None
                    def scalar(self): return False
                return MockResult()

            def begin(self):
                class MockTransaction:
                    def commit(self): pass
                    def rollback(self): pass
                return MockTransaction()

            def in_transaction(self): return False

        # Create workflow with mock session
        workflow = create_workflow(
            user_id="test_user_123",
            db_session=MockSession(),
            max_threads=4
        )

        # Override methods that require external services for testing
        original_nas_method = workflow._upload_batch_to_nas
        original_db_method = workflow._update_database_batch
        original_mockup_method = workflow._generate_mockups_batch

        def mock_nas_upload(images, batch_id):
            logger.info(f"🔄 Mock NAS upload for batch {batch_id}: {len(images)} images")
            for image in images:
                image.nas_uploaded = True
            return images

        def mock_db_update(images, batch_id):
            logger.info(f"🔄 Mock DB update for batch {batch_id}: {len(images)} images")
            for image in images:
                image.db_updated = True
            return images

        def mock_mockup_generation(images, batch_id):
            logger.info(f"🔄 Mock mockup generation for batch {batch_id}: {len(images)} images")
            for image in images:
                image.mockup_generated = True
            return images

        # Apply mocks
        workflow._upload_batch_to_nas = mock_nas_upload
        workflow._update_database_batch = mock_db_update
        workflow._generate_mockups_batch = mock_mockup_generation

        # Process images through workflow
        result = workflow.process_images(test_images)

        # Display results
        logger.info("📊 Workflow Test Results:")
        logger.info(f"   📸 Total images: {result.total_images}")
        logger.info(f"   ✅ Processed: {result.processed_images}")
        logger.info(f"   🔄 Skipped duplicates: {result.skipped_duplicates}")
        logger.info(f"   ❌ Errors: {result.errors}")
        logger.info(f"   ⏱️  Processing time: {result.processing_time:.2f}s")
        logger.info(f"   📤 NAS uploads: {result.nas_uploads}")
        logger.info(f"   🗄️  Database updates: {result.db_updates}")
        logger.info(f"   🎨 Mockups created: {result.mockups_created}")

        # Test passed if we processed some images and detected duplicates
        if result.processed_images > 0 and result.skipped_duplicates > 0:
            logger.info("🎉 Workflow test PASSED!")
            return True
        else:
            logger.warning("⚠️  Workflow test results unexpected")
            return False

    except Exception as e:
        logger.error(f"❌ Workflow test FAILED: {e}")
        return False

def main():
    """Main test function"""
    logger.info("🧪 Starting Image Upload Workflow Tests")

    # Test dependencies
    if not test_workflow_dependencies():
        logger.error("❌ Dependencies test failed")
        return False

    # Test workflow
    if not test_workflow():
        logger.error("❌ Workflow test failed")
        return False

    logger.info("🎉 All tests PASSED!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)