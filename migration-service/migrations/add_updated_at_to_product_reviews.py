"""
Add updated_at column to ecommerce_product_reviews table

This migration adds the missing updated_at column to match the ProductReview entity.
"""

from sqlalchemy import text
import logging

def upgrade(connection):
    """Add updated_at column to ecommerce_product_reviews."""
    try:
        logging.info("Checking ecommerce_product_reviews table for updated_at column...")

        # Check if table exists
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'ecommerce_product_reviews'
        """))

        if not result.fetchone():
            logging.info("Table doesn't exist yet, skipping migration")
            return

        # Check if updated_at column already exists
        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'ecommerce_product_reviews'
            AND column_name = 'updated_at'
        """))

        if result.fetchone():
            logging.info("updated_at column already exists, skipping")
            return

        # Add updated_at column
        logging.info("Adding updated_at column to ecommerce_product_reviews...")
        connection.execute(text("""
            ALTER TABLE ecommerce_product_reviews
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        """))

        logging.info("✅ Successfully added updated_at column to ecommerce_product_reviews")
        connection.commit()

    except Exception as e:
        logging.error(f"Error adding updated_at column to product reviews: {e}")
        raise e


def downgrade(connection):
    """Remove updated_at column from ecommerce_product_reviews."""
    try:
        logging.info("Removing updated_at column from ecommerce_product_reviews...")

        connection.execute(text("""
            ALTER TABLE ecommerce_product_reviews
            DROP COLUMN IF EXISTS updated_at
        """))

        logging.info("✅ Successfully removed updated_at column from ecommerce_product_reviews")
        connection.commit()

    except Exception as e:
        logging.error(f"Error removing updated_at column: {e}")
        raise e
