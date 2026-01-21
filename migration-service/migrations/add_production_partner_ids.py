"""
Add production_partner_ids column to etsy_product_templates

This migration adds support for Etsy API's production_partner_ids requirement
for physical listings. Empty/null means "ready to ship" (made by seller).
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add production_partner_ids column to etsy_product_templates table."""
    try:
        # Check if column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'etsy_product_templates' AND column_name = 'production_partner_ids'
        """))

        if not result.fetchone():
            # Add the new column
            connection.execute(text("""
                ALTER TABLE etsy_product_templates
                ADD COLUMN production_partner_ids TEXT
            """))
            logging.info("Added production_partner_ids column to etsy_product_templates table")

            # Add column comment
            connection.execute(text("""
                COMMENT ON COLUMN etsy_product_templates.production_partner_ids IS
                'Comma-separated list of production partner IDs. Empty/null means "ready to ship" (made by seller). Required for physical items in Etsy API.'
            """))
            logging.info("Added comment to production_partner_ids column")
        else:
            logging.info("production_partner_ids column already exists in etsy_product_templates table")

        # Analyze table to update statistics
        connection.execute(text("ANALYZE etsy_product_templates"))
        logging.info("Successfully completed production_partner_ids column migration")

    except Exception as e:
        logging.error(f"Error in production_partner_ids column migration: {e}")
        raise e

def downgrade(connection):
    """Remove production_partner_ids column from etsy_product_templates table."""
    try:
        # Drop the column
        connection.execute(text("""
            ALTER TABLE etsy_product_templates
            DROP COLUMN IF EXISTS production_partner_ids
        """))

        logging.info("Successfully removed production_partner_ids column from etsy_product_templates table")

    except Exception as e:
        logging.error(f"Error removing production_partner_ids column: {e}")
        raise e
