"""
Regenerate all Etsy design mockups with proper watermarks.

This migration is triggered by setting the environment variable:
REGENERATE_ETSY_MOCKUPS=true

It will:
1. Find all Etsy mockups in the database
2. Regenerate mockups for each design with proper watermarks
3. Update the mockup_images table with new paths
"""

import os
import logging
from sqlalchemy import text

def upgrade(connection):
    """Regenerate Etsy mockups with watermarks if env var is set."""

    # Check if migration should run
    should_run = os.getenv('REGENERATE_ETSY_MOCKUPS', 'false').lower() == 'true'

    if not should_run:
        logging.info("⏭️  Skipping Etsy mockup regeneration (REGENERATE_ETSY_MOCKUPS not set to 'true')")
        return

    logging.info("🔄 Starting Etsy mockup regeneration with watermarks...")

    # Check for required dependencies first
    try:
        import cv2
        import numpy
    except ImportError as e:
        logging.error(f"❌ Missing required dependencies for mockup regeneration: {e}")
        logging.error("📦 Please add opencv-python and numpy to migration-requirements.txt")
        logging.error("⏭️  Skipping mockup regeneration - run this after dependencies are installed")
        return

    # Import necessary modules (these also require cv2 to be installed)
    import sys
    sys.path.insert(0, '/app/server')
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'server'))

    try:
        from server.src.entities.mockup import Mockups, MockupImage
        from server.src.entities.designs import DesignImages
        from server.src.utils.mockups_util import create_mockups_for_etsy
        from sqlalchemy.orm import Session
    except ImportError as e:
        error_msg = str(e)
        if "PlatformConnection" in error_msg:
            logging.error(f"❌ Circular import issue with server entities: {error_msg}")
            logging.error("⚠️  This migration requires running from the main server context")
            logging.error("⏭️  Skipping mockup regeneration - run this migration separately if needed")
        elif "cv2" in error_msg or "numpy" in error_msg:
            logging.error(f"❌ Missing required dependencies for mockup regeneration: {error_msg}")
            logging.error("📦 Please add opencv-python and numpy to migration-requirements.txt")
            logging.error("⏭️  Skipping mockup regeneration")
        else:
            logging.error(f"❌ Failed to import server modules: {error_msg}")
            logging.error("⏭️  Skipping mockup regeneration")
        return

    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=connection.engine)
    db = SessionLocal()

    try:
        # Get watermark path from environment or use default
        default_watermark = os.getenv('WATERMARK_PATH', '/share/Graphics/FunnyBunny/Mockups/BaseMockups/Watermarks/Rectangle Watermark.png')
        logging.info(f"Using watermark: {default_watermark}")

        # Find all Etsy mockups (template_source = 'etsy' or NULL for legacy)
        mockups_query = db.query(Mockups).filter(
            (Mockups.template_source == 'etsy') | (Mockups.template_source == None)
        ).all()

        logging.info(f"Found {len(mockups_query)} Etsy mockups to regenerate")

        processed_count = 0
        failed_count = 0

        for mockup in mockups_query:
            try:
                # Get associated designs
                designs = db.query(DesignImages).filter(
                    DesignImages.id.in_([d.id for d in mockup.designs])
                ).all()

                if not designs:
                    logging.warning(f"⚠️  No designs found for mockup {mockup.id}, skipping")
                    continue

                # Get user shop_name for root path (using raw SQL to avoid circular imports)
                user_result = connection.execute(
                    text("SELECT shop_name FROM users WHERE id = :user_id"),
                    {"user_id": str(mockup.user_id)}
                )
                user_row = user_result.fetchone()
                if not user_row:
                    logging.warning(f"⚠️  No user found for mockup {mockup.id}, skipping")
                    continue

                # Determine root path
                shop_name = user_row[0] or 'DefaultShop'
                root_path = f"/share/Graphics/{shop_name}/"

                # Get template name
                template_name = mockup.template.name if mockup.template else 'UVDTF 16oz'

                # Build mask data from mockup
                mask_data = {}
                for mockup_image in mockup.mockup_images:
                    mask_data[mockup_image.id] = {
                        'masks': mockup_image.mask_data,
                        'points': mockup_image.points if hasattr(mockup_image, 'points') else []
                    }

                logging.info(f"🔄 Regenerating mockup {mockup.id} for {len(designs)} designs with template {template_name}")

                # Regenerate mockups with watermark
                _, mockup_return, _ = create_mockups_for_etsy(
                    designs=designs,
                    mockup=mockup,
                    template_name=template_name,
                    root_path=root_path,
                    mask_data=mask_data
                )

                # Update mockup_images table with watermark path
                for mockup_image in mockup.mockup_images:
                    mockup_image.watermark_path = default_watermark

                db.commit()
                processed_count += 1
                logging.info(f"✅ Successfully regenerated mockup {mockup.id}")

            except Exception as e:
                logging.error(f"❌ Failed to regenerate mockup {mockup.id}: {e}")
                failed_count += 1
                db.rollback()
                continue

        logging.info(f"✅ Completed Etsy mockup regeneration:")
        logging.info(f"   - Processed: {processed_count}")
        logging.info(f"   - Failed: {failed_count}")
        logging.info(f"   - Total: {len(mockups_query)}")

    finally:
        db.close()


def downgrade(connection):
    """This migration cannot be downgraded."""
    logging.info("⏭️  Skipping downgrade for mockup regeneration (cannot revert)")
    pass
