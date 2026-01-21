"""
Add shopify_product_templates table

This migration creates the shopify_product_templates table to store
Shopify product template configurations for product creation.
"""

from sqlalchemy import text
import logging
import os

# Check if multi-tenant is enabled
MULTI_TENANT_ENABLED = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'

def upgrade(connection):
    """Create shopify_product_templates table."""
    try:
        # Check if table already exists
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'shopify_product_templates'
        """))

        if not result.fetchone():
            # Create the table - always include org_id for consistency
            # even if multi-tenant is not enabled (will be NULL)
            connection.execute(text("""
                CREATE TABLE shopify_product_templates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    org_id UUID,

                    -- Template metadata
                    name VARCHAR NOT NULL,

                    -- Product details
                    template_title VARCHAR NOT NULL,
                    description TEXT,
                    vendor VARCHAR,
                    product_type VARCHAR,
                    tags TEXT,

                    -- Pricing
                    price FLOAT NOT NULL,
                    compare_at_price FLOAT,
                    cost_per_item FLOAT,

                    -- Inventory & Shipping
                    sku_prefix VARCHAR,
                    barcode_prefix VARCHAR,
                    track_inventory BOOLEAN DEFAULT TRUE,
                    inventory_quantity INTEGER DEFAULT 0,
                    inventory_policy VARCHAR DEFAULT 'deny',
                    fulfillment_service VARCHAR DEFAULT 'manual',
                    requires_shipping BOOLEAN DEFAULT TRUE,
                    weight FLOAT,
                    weight_unit VARCHAR DEFAULT 'g',

                    -- Product options/variants
                    has_variants BOOLEAN DEFAULT FALSE,
                    option1_name VARCHAR,
                    option1_values TEXT,
                    option2_name VARCHAR,
                    option2_values TEXT,
                    option3_name VARCHAR,
                    option3_values TEXT,

                    -- Publishing & SEO
                    status VARCHAR DEFAULT 'draft',
                    published_scope VARCHAR DEFAULT 'web',
                    seo_title VARCHAR,
                    seo_description TEXT,

                    -- Tax settings
                    is_taxable BOOLEAN DEFAULT TRUE,
                    tax_code VARCHAR,

                    -- Additional settings
                    gift_card BOOLEAN DEFAULT FALSE,
                    template_suffix VARCHAR,

                    -- Timestamps
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE
                )
            """))
            logging.info("Created shopify_product_templates table")

            # Add foreign key constraint for org_id if organizations table exists
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

            # Add indexes
            connection.execute(text("""
                CREATE INDEX idx_shopify_product_templates_user_id
                ON shopify_product_templates(user_id)
            """))
            logging.info("Created index on user_id")

            # Always create org_id index since column always exists
            connection.execute(text("""
                CREATE INDEX idx_shopify_product_templates_org_id
                ON shopify_product_templates(org_id)
            """))
            logging.info("Created index on org_id")

            connection.execute(text("""
                CREATE INDEX idx_shopify_product_templates_name
                ON shopify_product_templates(name)
            """))
            logging.info("Created index on name")

            # Add comments
            connection.execute(text("""
                COMMENT ON TABLE shopify_product_templates IS
                'Stores Shopify product template configurations for automated product creation'
            """))

            connection.execute(text("""
                COMMENT ON COLUMN shopify_product_templates.template_title IS
                'Product title template (can include {design_name} placeholder)'
            """))

            connection.execute(text("""
                COMMENT ON COLUMN shopify_product_templates.tags IS
                'Comma-separated tags for the product'
            """))

            connection.execute(text("""
                COMMENT ON COLUMN shopify_product_templates.option1_values IS
                'Comma-separated values for option 1 (e.g., Small,Medium,Large)'
            """))

            connection.execute(text("""
                COMMENT ON COLUMN shopify_product_templates.option2_values IS
                'Comma-separated values for option 2'
            """))

            connection.execute(text("""
                COMMENT ON COLUMN shopify_product_templates.option3_values IS
                'Comma-separated values for option 3'
            """))

            # Analyze table to update statistics
            connection.execute(text("ANALYZE shopify_product_templates"))
            logging.info("Successfully completed shopify_product_templates table migration")

        else:
            logging.info("shopify_product_templates table already exists")

    except Exception as e:
        logging.error(f"Error in shopify_product_templates table migration: {e}")
        raise e

def downgrade(connection):
    """Drop shopify_product_templates table."""
    try:
        # Drop the table
        connection.execute(text("""
            DROP TABLE IF EXISTS shopify_product_templates CASCADE
        """))

        logging.info("Successfully dropped shopify_product_templates table")

    except Exception as e:
        logging.error(f"Error dropping shopify_product_templates table: {e}")
        raise e
