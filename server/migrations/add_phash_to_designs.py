"""
Add phash column to design_images table

This migration adds a phash column to store perceptual hashes
for efficient duplicate detection without reading files from disk.
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add phash column to design_images table."""
    try:
        # Check if phash column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'design_images' AND column_name = 'phash'
        """))

        if not result.fetchone():
            # Add the new column
            connection.execute(text("""
                ALTER TABLE design_images ADD COLUMN phash VARCHAR(64);
            """))
            logging.info("Added phash column to design_images table")
        else:
            logging.info("phash column already exists in design_images table")

        # Check if index already exists
        result = connection.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'design_images' AND indexname = 'idx_design_images_phash'
        """))

        if not result.fetchone():
            # Add index for faster lookups
            connection.execute(text("""
                CREATE INDEX idx_design_images_phash ON design_images(phash) WHERE phash IS NOT NULL;
            """))
            logging.info("Added index for phash column")
        else:
            logging.info("phash index already exists")

        logging.info("Successfully completed phash column migration")

    except Exception as e:
        logging.error(f"Error in phash column migration: {e}")
        raise e

def downgrade(connection):
    """Remove phash column from design_images table."""
    try:
        # Drop index first
        connection.execute(text("""
            DROP INDEX IF EXISTS idx_design_images_phash;
        """))

        # Drop the column
        connection.execute(text("""
            ALTER TABLE design_images DROP COLUMN IF EXISTS phash;
        """))

        logging.info("Successfully removed phash column and index from design_images table")

    except Exception as e:
        logging.error(f"Error removing phash column: {e}")
        raise e