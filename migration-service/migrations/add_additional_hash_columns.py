"""
Add additional hash columns to design_images table

This migration adds ahash, dhash, and whash columns to the design_images table
to support enhanced multi-hash duplicate detection.

Background:
- phash (perceptual hash) already exists
- Adding ahash (average hash), dhash (difference hash), whash (wavelet hash)
- These provide better duplicate detection accuracy using multiple algorithms
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add ahash, dhash, and whash columns to design_images table."""
    try:
        logging.info("Starting additional hash columns migration...")

        # List of new hash columns to add
        hash_columns = [
            ('ahash', 'Average Hash for duplicate detection'),
            ('dhash', 'Difference Hash for duplicate detection'),
            ('whash', 'Wavelet Hash for duplicate detection')
        ]

        columns_added = 0

        for column_name, description in hash_columns:
            # Check if column already exists
            result = connection.execute(text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'design_images' AND column_name = '{column_name}'
            """))

            if not result.fetchone():
                # Add the new column
                connection.execute(text(f"""
                    ALTER TABLE design_images ADD COLUMN {column_name} VARCHAR(64);
                """))
                logging.info(f"Added {column_name} column to design_images table")
                columns_added += 1

                # Add comment to column for documentation
                connection.execute(text(f"""
                    COMMENT ON COLUMN design_images.{column_name} IS '{description}';
                """))
                logging.info(f"Added comment to {column_name} column")
            else:
                logging.info(f"{column_name} column already exists in design_images table")

        # Create composite index for all hash columns for efficient duplicate detection
        index_name = 'idx_design_images_all_hashes'
        result = connection.execute(text(f"""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'design_images' AND indexname = '{index_name}'
        """))

        if not result.fetchone():
            connection.execute(text(f"""
                CREATE INDEX {index_name} ON design_images(phash, ahash, dhash, whash)
                WHERE phash IS NOT NULL OR ahash IS NOT NULL OR dhash IS NOT NULL OR whash IS NOT NULL;
            """))
            logging.info(f"Added composite index {index_name} for all hash columns")
        else:
            logging.info(f"Composite index {index_name} already exists")

        # Create individual indexes for each new hash column
        for column_name, _ in hash_columns:
            index_name = f'idx_design_images_{column_name}'
            result = connection.execute(text(f"""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'design_images' AND indexname = '{index_name}'
            """))

            if not result.fetchone():
                connection.execute(text(f"""
                    CREATE INDEX {index_name} ON design_images({column_name})
                    WHERE {column_name} IS NOT NULL;
                """))
                logging.info(f"Added index {index_name} for {column_name} column")
            else:
                logging.info(f"Index {index_name} already exists")

        # Summary
        logging.info("=" * 60)
        logging.info("ADDITIONAL HASH COLUMNS MIGRATION SUMMARY")
        logging.info("=" * 60)
        logging.info(f"New columns added: {columns_added}")
        logging.info("Hash columns now available: phash, ahash, dhash, whash")
        logging.info("Indexes created for efficient duplicate detection")

        # Verify the table structure
        result = connection.execute(text("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'design_images'
            AND column_name IN ('phash', 'ahash', 'dhash', 'whash')
            ORDER BY column_name;
        """))

        columns_info = result.fetchall()
        logging.info("Current hash columns in design_images table:")
        for column_name, data_type, max_length in columns_info:
            logging.info(f"  - {column_name}: {data_type}({max_length})")

        logging.info("✅ Additional hash columns migration completed successfully!")

    except Exception as e:
        logging.error(f"Error in additional hash columns migration: {e}")
        raise e

def downgrade(connection):
    """Remove additional hash columns from design_images table."""
    try:
        logging.info("Starting downgrade of additional hash columns...")

        # List of columns to remove (keep phash as it was there originally)
        columns_to_remove = ['ahash', 'dhash', 'whash']

        # Drop indexes first
        indexes_to_remove = [
            'idx_design_images_all_hashes',
            'idx_design_images_ahash',
            'idx_design_images_dhash',
            'idx_design_images_whash'
        ]

        for index_name in indexes_to_remove:
            connection.execute(text(f"""
                DROP INDEX IF EXISTS {index_name};
            """))
            logging.info(f"Dropped index {index_name}")

        # Drop the columns
        for column_name in columns_to_remove:
            connection.execute(text(f"""
                ALTER TABLE design_images DROP COLUMN IF EXISTS {column_name};
            """))
            logging.info(f"Dropped column {column_name}")

        logging.info("✅ Successfully removed additional hash columns and indexes from design_images table")

    except Exception as e:
        logging.error(f"Error removing additional hash columns: {e}")
        raise e