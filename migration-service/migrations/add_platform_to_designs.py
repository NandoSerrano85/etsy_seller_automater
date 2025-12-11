"""
Add platform column to design_images table

This migration adds a platform column to distinguish between Shopify and Etsy designs,
allowing users to have the same design in both platforms without triggering duplicate detection.
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add platform column to design_images table."""
    try:
        # Check if platform column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'design_images' AND column_name = 'platform'
        """))

        if not result.fetchone():
            # Add the new column with default 'etsy' for backward compatibility
            connection.execute(text("""
                ALTER TABLE design_images ADD COLUMN platform VARCHAR(20) DEFAULT 'etsy' NOT NULL;
            """))
            logging.info("Added platform column to design_images table")
        else:
            logging.info("platform column already exists in design_images table")

        # Check if index already exists
        result = connection.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'design_images' AND indexname = 'idx_design_images_platform'
        """))

        if not result.fetchone():
            # Add index for faster lookups when filtering by platform
            connection.execute(text("""
                CREATE INDEX idx_design_images_platform ON design_images(platform);
            """))
            logging.info("Added index for platform column")
        else:
            logging.info("platform index already exists")

        # Add composite index for user_id + platform + phash for duplicate detection
        result = connection.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'design_images' AND indexname = 'idx_design_images_user_platform_phash'
        """))

        if not result.fetchone():
            connection.execute(text("""
                CREATE INDEX idx_design_images_user_platform_phash
                ON design_images(user_id, platform, phash)
                WHERE phash IS NOT NULL AND is_active = true;
            """))
            logging.info("Added composite index for user_id + platform + phash")
        else:
            logging.info("Composite index for user_id + platform + phash already exists")

        logging.info("Successfully completed platform column migration")

    except Exception as e:
        logging.error(f"Error in platform column migration: {e}")
        raise e

def downgrade(connection):
    """Remove platform column from design_images table."""
    try:
        # Drop indexes first
        connection.execute(text("""
            DROP INDEX IF EXISTS idx_design_images_user_platform_phash;
        """))

        connection.execute(text("""
            DROP INDEX IF EXISTS idx_design_images_platform;
        """))

        # Drop the column
        connection.execute(text("""
            ALTER TABLE design_images DROP COLUMN IF EXISTS platform;
        """))

        logging.info("Successfully removed platform column and indexes from design_images table")

    except Exception as e:
        logging.error(f"Error removing platform column: {e}")
        raise e
