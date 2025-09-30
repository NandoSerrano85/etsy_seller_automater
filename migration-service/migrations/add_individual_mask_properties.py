#!/usr/bin/env python3
"""
Migration: Add individual mask properties to mockup_mask_data table

This migration adds is_cropped_list and alignment_list columns to support
individual cropping and alignment settings for each mask, instead of
using a single setting for all masks in a mask data group.

The new columns are JSON arrays that store boolean and string values
respectively for each mask.
"""

import logging
from sqlalchemy import text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def upgrade(conn):
    """Add individual mask properties columns to mockup_mask_data table"""
    logger.info("Starting individual mask properties migration...")

    try:
        # Add new columns for individual mask properties
        logger.info("Adding is_cropped_list column...")
        conn.execute(text("""
            ALTER TABLE mockup_mask_data
            ADD COLUMN IF NOT EXISTS is_cropped_list JSON;
        """))

        logger.info("Adding alignment_list column...")
        conn.execute(text("""
            ALTER TABLE mockup_mask_data
            ADD COLUMN IF NOT EXISTS alignment_list JSON;
        """))

        # Update existing records to populate the new columns
        logger.info("Populating new columns with existing data...")
        conn.execute(text("""
            UPDATE mockup_mask_data
            SET
                is_cropped_list = (
                    SELECT json_agg(is_cropped)
                    FROM generate_series(1, json_array_length(masks))
                ),
                alignment_list = (
                    SELECT json_agg(alignment)
                    FROM generate_series(1, json_array_length(masks))
                )
            WHERE is_cropped_list IS NULL OR alignment_list IS NULL;
        """))

        # Add comments to document the new columns
        conn.execute(text("""
            COMMENT ON COLUMN mockup_mask_data.is_cropped_list IS
            'JSON array of boolean values for individual mask cropping settings';
        """))

        conn.execute(text("""
            COMMENT ON COLUMN mockup_mask_data.alignment_list IS
            'JSON array of string values for individual mask alignment settings';
        """))

        logger.info("✅ Individual mask properties migration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error during individual mask properties migration: {e}")
        raise

def downgrade(conn):
    """Remove individual mask properties columns"""
    logger.info("Starting individual mask properties migration rollback...")

    try:
        logger.info("Removing is_cropped_list column...")
        conn.execute(text("""
            ALTER TABLE mockup_mask_data
            DROP COLUMN IF EXISTS is_cropped_list;
        """))

        logger.info("Removing alignment_list column...")
        conn.execute(text("""
            ALTER TABLE mockup_mask_data
            DROP COLUMN IF EXISTS alignment_list;
        """))

        logger.info("✅ Individual mask properties migration rollback completed!")

    except Exception as e:
        logger.error(f"❌ Error during individual mask properties migration rollback: {e}")
        raise

if __name__ == "__main__":
    import os
    import sys
    from sqlalchemy import create_engine

    # Get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    try:
        engine = create_engine(database_url)
        logger.info("✅ Connected to database")

        with engine.connect() as conn:
            trans = conn.begin()
            try:
                upgrade(conn)
                trans.commit()
                logger.info("🎉 Migration completed successfully!")
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Migration failed: {e}")
                raise

    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        sys.exit(1)