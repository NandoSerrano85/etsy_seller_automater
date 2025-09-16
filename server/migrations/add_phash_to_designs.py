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
        # Add the new column
        connection.execute(text("""
            ALTER TABLE design_images ADD COLUMN phash VARCHAR(64);
        """))

        # Add index for faster lookups
        connection.execute(text("""
            CREATE INDEX idx_design_images_phash ON design_images(phash) WHERE phash IS NOT NULL;
        """))

        logging.info("Successfully added phash column and index to design_images table")

    except Exception as e:
        logging.error(f"Error adding phash column: {e}")
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