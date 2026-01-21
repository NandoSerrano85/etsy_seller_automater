"""
Add org_id column to shopify_product_templates if it doesn't exist

This migration ensures org_id column exists in shopify_product_templates
for consistency, regardless of MULTI_TENANT_ENABLED setting.
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add org_id column to shopify_product_templates if it doesn't exist."""
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

        # Check if org_id column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'shopify_product_templates' AND column_name = 'org_id'
        """))

        if not result.fetchone():
            # Add the org_id column
            connection.execute(text("""
                ALTER TABLE shopify_product_templates
                ADD COLUMN org_id UUID
            """))
            logging.info("Added org_id column to shopify_product_templates table")

            # Add foreign key constraint if organizations table exists
            org_table_check = connection.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'organizations'
            """))

            if org_table_check.fetchone():
                connection.execute(text("""
                    ALTER TABLE shopify_product_templates
                    ADD CONSTRAINT fk_shopify_templates_org
                    FOREIGN KEY (org_id)
                    REFERENCES organizations(id)
                    ON DELETE CASCADE
                """))
                logging.info("Added foreign key constraint for org_id")

            # Add index on org_id
            connection.execute(text("""
                CREATE INDEX idx_shopify_product_templates_org_id
                ON shopify_product_templates(org_id)
            """))
            logging.info("Added index on org_id")

        else:
            logging.info("org_id column already exists in shopify_product_templates table")

        # Analyze table to update statistics
        connection.execute(text("ANALYZE shopify_product_templates"))
        logging.info("Successfully completed org_id column migration for shopify_product_templates")

    except Exception as e:
        logging.error(f"Error in org_id column migration for shopify_product_templates: {e}")
        raise e

def downgrade(connection):
    """Remove org_id column from shopify_product_templates table."""
    try:
        # Drop the constraint first if it exists
        connection.execute(text("""
            ALTER TABLE shopify_product_templates
            DROP CONSTRAINT IF EXISTS fk_shopify_templates_org
        """))

        # Drop the index if it exists
        connection.execute(text("""
            DROP INDEX IF EXISTS idx_shopify_product_templates_org_id
        """))

        # Drop the column
        connection.execute(text("""
            ALTER TABLE shopify_product_templates
            DROP COLUMN IF EXISTS org_id
        """))

        logging.info("Successfully removed org_id column from shopify_product_templates table")

    except Exception as e:
        logging.error(f"Error removing org_id column from shopify_product_templates: {e}")
        raise e
