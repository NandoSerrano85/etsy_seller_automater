"""
Add AI tagging columns to design_images table

This migration adds tags and tags_metadata columns for automatic image tagging.
Supports both AI mode (OpenAI) and basic mode (OCR + colors + filename).
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add tags columns to design_images table."""
    try:
        # Check if tags column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'design_images' AND column_name = 'tags'
        """))

        if not result.fetchone():
            # Add the tags column (JSONB array)
            connection.execute(text("""
                ALTER TABLE design_images
                ADD COLUMN tags JSONB DEFAULT '[]'::jsonb;
            """))
            logging.info("✓ Added tags column to design_images table")
        else:
            logging.info("ℹ️  tags column already exists in design_images table")

        # Check if tags_metadata column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'design_images' AND column_name = 'tags_metadata'
        """))

        if not result.fetchone():
            # Add the tags_metadata column (JSONB object)
            connection.execute(text("""
                ALTER TABLE design_images
                ADD COLUMN tags_metadata JSONB;
            """))
            logging.info("✓ Added tags_metadata column to design_images table")
        else:
            logging.info("ℹ️  tags_metadata column already exists in design_images table")

        # Check if index already exists
        result = connection.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'design_images' AND indexname = 'idx_design_images_tags'
        """))

        if not result.fetchone():
            # Add GIN index for efficient JSONB tag queries
            connection.execute(text("""
                CREATE INDEX idx_design_images_tags
                ON design_images USING gin(tags);
            """))
            logging.info("✓ Added GIN index for tags column")
        else:
            logging.info("ℹ️  tags index already exists")

        # Add column comments for documentation
        connection.execute(text("""
            COMMENT ON COLUMN design_images.tags IS
            'AI-generated tags for searchability (text, objects, style, colors)';
        """))
        connection.execute(text("""
            COMMENT ON COLUMN design_images.tags_metadata IS
            'Metadata about tag generation (model, processing time, categories, confidence)';
        """))

        logging.info("✅ Successfully completed tags column migration")

    except Exception as e:
        logging.error(f"❌ Error in tags column migration: {e}")
        raise e

def downgrade(connection):
    """Remove tags columns from design_images table."""
    try:
        # Drop index first
        connection.execute(text("""
            DROP INDEX IF EXISTS idx_design_images_tags;
        """))
        logging.info("✓ Dropped tags index")

        # Drop the columns
        connection.execute(text("""
            ALTER TABLE design_images DROP COLUMN IF EXISTS tags;
        """))
        logging.info("✓ Dropped tags column")

        connection.execute(text("""
            ALTER TABLE design_images DROP COLUMN IF EXISTS tags_metadata;
        """))
        logging.info("✓ Dropped tags_metadata column")

        logging.info("✅ Successfully removed tags columns and index from design_images table")

    except Exception as e:
        logging.error(f"❌ Error removing tags columns: {e}")
        raise e
