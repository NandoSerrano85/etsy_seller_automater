"""
Add variant_configs column to shopify_product_templates

This migration adds a JSON column to store complex nested variant configurations
including per-variant pricing, weights, SKUs, country of origin, and HS codes.
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add variant_configs JSON column to shopify_product_templates."""
    try:
        # Check if table exists first
        table_check = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'shopify_product_templates'
        """))

        if not table_check.fetchone():
            logging.info("shopify_product_templates table doesn't exist yet, skipping")
            return

        # Check if variant_configs column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'shopify_product_templates' AND column_name = 'variant_configs'
        """))

        if not result.fetchone():
            # Add the variant_configs column
            connection.execute(text("""
                ALTER TABLE shopify_product_templates
                ADD COLUMN variant_configs JSON
            """))
            logging.info("Added variant_configs column to shopify_product_templates table")

            # Add comment
            connection.execute(text("""
                COMMENT ON COLUMN shopify_product_templates.variant_configs IS
                'JSON array storing complex variant configurations with nested options, pricing, weights, SKUs, country of origin, and HS codes'
            """))
            logging.info("Added comment to variant_configs column")

        else:
            logging.info("variant_configs column already exists in shopify_product_templates table")

        # Analyze table to update statistics
        connection.execute(text("ANALYZE shopify_product_templates"))
        logging.info("Successfully completed variant_configs column migration for shopify_product_templates")

    except Exception as e:
        logging.error(f"Error in variant_configs column migration for shopify_product_templates: {e}")
        raise e

def downgrade(connection):
    """Remove variant_configs column from shopify_product_templates table."""
    try:
        # Drop the column
        connection.execute(text("""
            ALTER TABLE shopify_product_templates
            DROP COLUMN IF EXISTS variant_configs
        """))

        logging.info("Successfully removed variant_configs column from shopify_product_templates table")

    except Exception as e:
        logging.error(f"Error removing variant_configs column from shopify_product_templates: {e}")
        raise e
