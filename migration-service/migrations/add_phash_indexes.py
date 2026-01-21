"""
Add indexes for perceptual hash duplicate detection

This migration adds indexes for fast lookups on phash, ahash, dhash, and whash columns
to optimize duplicate image detection queries.
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add indexes for hash columns to enable fast lookups."""
    try:
        # List of indexes to create
        indexes = [
            ('idx_design_images_phash', 'phash'),
            ('idx_design_images_ahash', 'ahash'),
            ('idx_design_images_dhash', 'dhash'),
            ('idx_design_images_whash', 'whash'),
        ]

        for index_name, column_name in indexes:
            # Check if index already exists
            result = connection.execute(text(f"""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'design_images' AND indexname = '{index_name}'
            """))

            if not result.fetchone():
                # Create index
                connection.execute(text(f"""
                    CREATE INDEX {index_name}
                    ON design_images({column_name})
                    WHERE {column_name} IS NOT NULL AND is_active = true
                """))
                logging.info(f"Created index {index_name} on design_images.{column_name}")
            else:
                logging.info(f"Index {index_name} already exists")

        # Check if composite index exists
        result = connection.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'design_images' AND indexname = 'idx_design_images_user_active'
        """))

        if not result.fetchone():
            # Create composite index for user-specific queries
            connection.execute(text("""
                CREATE INDEX idx_design_images_user_active
                ON design_images(user_id, is_active)
                WHERE is_active = true
            """))
            logging.info("Created composite index idx_design_images_user_active")
        else:
            logging.info("Composite index idx_design_images_user_active already exists")

        # Analyze table to update statistics
        connection.execute(text("ANALYZE design_images"))
        logging.info("Successfully completed phash indexes migration")

    except Exception as e:
        logging.error(f"Error in phash indexes migration: {e}")
        raise e

def downgrade(connection):
    """Remove hash column indexes."""
    try:
        # Drop all indexes
        indexes = [
            'idx_design_images_phash',
            'idx_design_images_ahash',
            'idx_design_images_dhash',
            'idx_design_images_whash',
            'idx_design_images_user_active'
        ]

        for index_name in indexes:
            connection.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
            logging.info(f"Dropped index {index_name}")

        logging.info("Successfully removed phash indexes from design_images table")

    except Exception as e:
        logging.error(f"Error removing phash indexes: {e}")
        raise e
