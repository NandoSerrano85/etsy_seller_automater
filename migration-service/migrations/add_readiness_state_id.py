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
            WHERE table_name = 'etsy_product_templates' AND column_name = 'readiness_state_id'
        """))

        if not result.fetchone():
            # Add the new column
            connection.execute(text("""
                ALTER TABLE etsy_product_templates
                ADD COLUMN readiness_state_id INTEGER
            """))
            logging.info("Added readiness_state_id column to etsy_product_templates table")

            # Add column comment
            connection.execute(text("""
                COMMENT ON COLUMN etsy_product_templates.readiness_state_id IS
                'The numeric ID of the processing profile associated with the listing. Returned only when the listing is active and of type physical, and the endpoint is either shop-scoped (path contains shop_id) or a single-listing request such as getListing. For every other case this field can be null. Required for physical items in Etsy API.'
            """))
            logging.info("Added comment to readiness_state_id column")
        else:
            logging.info("readiness_state_id column already exists in etsy_product_templates table")

        # Analyze table to update statistics
        connection.execute(text("ANALYZE etsy_product_templates"))
        logging.info("Successfully completed readiness_state_id column migration")

    except Exception as e:
        logging.error(f"Error in readiness_state_id column migration: {e}")
        raise e

def downgrade(connection):
    """Remove readiness_state_id column from etsy_product_templates table."""
    try:
        # Drop the column
        connection.execute(text("""
            ALTER TABLE etsy_product_templates
            DROP COLUMN IF EXISTS readiness_state_id
        """))

        logging.info("Successfully removed readiness_state_id column from etsy_product_templates table")

    except Exception as e:
        logging.error(f"Error removing readiness_state_id column: {e}")
        raise e
