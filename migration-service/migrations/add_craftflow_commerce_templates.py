"""
Add CraftFlow Commerce templates and update mockups to support multiple template sources.

This migration:
1. Creates the craftflow_commerce_templates table
2. Adds template_source and new template foreign keys to mockups table
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add CraftFlow Commerce templates and update mockups."""
    try:
        logging.info("Adding CraftFlow Commerce templates support...")

        # Check if craftflow_commerce_templates table already exists
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'craftflow_commerce_templates'
        """))

        if not result.fetchone():
            logging.info("Creating craftflow_commerce_templates table...")
            connection.execute(text("""
                CREATE TABLE craftflow_commerce_templates (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id),
                    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                    name VARCHAR NOT NULL,
                    template_title VARCHAR NOT NULL,
                    description TEXT,
                    short_description VARCHAR(500),
                    product_type VARCHAR NOT NULL,
                    print_method VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    price FLOAT NOT NULL,
                    compare_at_price FLOAT,
                    cost FLOAT,
                    track_inventory BOOLEAN DEFAULT FALSE,
                    inventory_quantity INTEGER DEFAULT 0,
                    allow_backorder BOOLEAN DEFAULT FALSE,
                    digital_file_url VARCHAR,
                    download_limit INTEGER DEFAULT 3,
                    meta_title VARCHAR,
                    meta_description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_featured BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logging.info("✅ Created craftflow_commerce_templates table")
        else:
            logging.info("craftflow_commerce_templates table already exists, skipping")

        # Check if template_source column exists in mockups
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'mockups' AND column_name = 'template_source'
        """))

        if not result.fetchone():
            logging.info("Adding template_source column to mockups...")
            connection.execute(text("""
                ALTER TABLE mockups
                ADD COLUMN template_source VARCHAR DEFAULT 'etsy' NOT NULL
            """))
            logging.info("✅ Added template_source column")
        else:
            logging.info("template_source column already exists in mockups")

        # Check if shopify_template_id column exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'mockups' AND column_name = 'shopify_template_id'
        """))

        if not result.fetchone():
            logging.info("Adding shopify_template_id column to mockups...")
            connection.execute(text("""
                ALTER TABLE mockups
                ADD COLUMN shopify_template_id UUID REFERENCES shopify_product_templates(id)
            """))
            logging.info("✅ Added shopify_template_id column")
        else:
            logging.info("shopify_template_id column already exists in mockups")

        # Check if craftflow_template_id column exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'mockups' AND column_name = 'craftflow_template_id'
        """))

        if not result.fetchone():
            logging.info("Adding craftflow_template_id column to mockups...")
            connection.execute(text("""
                ALTER TABLE mockups
                ADD COLUMN craftflow_template_id UUID REFERENCES craftflow_commerce_templates(id)
            """))
            logging.info("✅ Added craftflow_template_id column")
        else:
            logging.info("craftflow_template_id column already exists in mockups")

        # Make product_template_id nullable if it isn't already
        logging.info("Making product_template_id nullable in mockups...")
        connection.execute(text("""
            ALTER TABLE mockups
            ALTER COLUMN product_template_id DROP NOT NULL
        """))
        logging.info("✅ Made product_template_id nullable")

        logging.info("✅ Successfully added CraftFlow Commerce templates support")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error adding CraftFlow Commerce templates: {e}")
        raise e


def downgrade(connection):
    """Remove CraftFlow Commerce templates and revert mockups changes."""
    try:
        logging.info("Removing CraftFlow Commerce templates support...")

        # Remove columns from mockups
        connection.execute(text("""
            ALTER TABLE mockups
            DROP COLUMN IF EXISTS craftflow_template_id,
            DROP COLUMN IF EXISTS shopify_template_id,
            DROP COLUMN IF EXISTS template_source
        """))

        # Drop craftflow_commerce_templates table
        connection.execute(text("""
            DROP TABLE IF EXISTS craftflow_commerce_templates CASCADE
        """))

        # Make product_template_id not nullable again
        connection.execute(text("""
            ALTER TABLE mockups
            ALTER COLUMN product_template_id SET NOT NULL
        """))

        logging.info("✅ Successfully removed CraftFlow Commerce templates support")
        # Note: Transaction is managed by migration runner, don't commit here

    except Exception as e:
        logging.error(f"Error removing CraftFlow Commerce templates: {e}")
        raise e
